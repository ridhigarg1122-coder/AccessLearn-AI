"""
AccessLearn AI - complete backend in one file.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:8000 in Chrome or Edge.

Keep index.html in the same folder as this file.
"""

from __future__ import annotations

import csv
import hashlib
import hmac
import io
import os
import re
import uuid
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import (
    APIRouter, Depends, FastAPI, File, HTTPException, Query, UploadFile,
    WebSocket, WebSocketDisconnect, status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import (
    JSON, DateTime, Float, ForeignKey, Integer, String, Text,
    UniqueConstraint, create_engine, select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker,
)

# =============================================================================
# 1. SETTINGS  (everything can be overridden by environment variables)
# =============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./accesslearn.db")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "720"))
AUDIO_DIR = os.getenv("AUDIO_STORAGE_DIR", "./audio_store")
MAX_AUDIO_MB = int(os.getenv("MAX_AUDIO_MB", "100"))
SUMMARY_DEBOUNCE_SEGMENTS = int(os.getenv("SUMMARY_DEBOUNCE_SEGMENTS", "5"))
TRANSLATION_PROVIDER = os.getenv("TRANSLATION_PROVIDER", "local")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local")
ASR_PROVIDER = os.getenv("ASR_PROVIDER", "browser")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# 2. DATABASE
# =============================================================================

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(20), default="teacher")
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Lecture(Base):
    __tablename__ = "lectures"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    source_language: Mapped[str] = mapped_column(String(10), default="en")
    status: Mapped[str] = mapped_column(String(20), default="created")
    is_demo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    segments: Mapped[list["TranscriptSegment"]] = relationship(
        back_populates="lecture", cascade="all, delete-orphan")


class AudioFile(Base):
    __tablename__ = "audio_files"
    id: Mapped[int] = mapped_column(primary_key=True)
    lecture_id: Mapped[int] = mapped_column(ForeignKey("lectures.id"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(100), default="")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TranscriptSegment(Base):
    """Only FINALISED speech is stored. Interim captions never reach this table."""
    __tablename__ = "transcript_segments"
    __table_args__ = (
        UniqueConstraint("lecture_id", "client_segment_id", name="uq_segment_client_id"),
        UniqueConstraint("lecture_id", "sequence_no", name="uq_segment_sequence"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    lecture_id: Mapped[int] = mapped_column(ForeignKey("lectures.id"), index=True)
    client_segment_id: Mapped[str] = mapped_column(String(64), index=True)
    sequence_no: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)          # raw, server side only
    masked_text: Mapped[str] = mapped_column(Text)   # what students may see
    language: Mapped[str] = mapped_column(String(10), default="en")
    start_ms: Mapped[int] = mapped_column(Integer, default=0)
    end_ms: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    lecture: Mapped[Lecture] = relationship(back_populates="segments")
    translations: Mapped[list["Translation"]] = relationship(
        back_populates="segment", cascade="all, delete-orphan")


class Translation(Base):
    __tablename__ = "translations"
    __table_args__ = (UniqueConstraint("segment_id", "target_language", name="uq_translation_lang"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    segment_id: Mapped[int] = mapped_column(ForeignKey("transcript_segments.id"), index=True)
    target_language: Mapped[str] = mapped_column(String(10))
    text: Mapped[str] = mapped_column(Text)
    masked_text: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(50), default="local")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    segment: Mapped[TranscriptSegment] = relationship(back_populates="translations")


class Summary(Base):
    __tablename__ = "summaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    lecture_id: Mapped[int] = mapped_column(ForeignKey("lectures.id"), index=True)
    summary_type: Mapped[str] = mapped_column(String(20), default="short")
    reading_level: Mapped[str] = mapped_column(String(20), default="high_school")
    content: Mapped[str] = mapped_column(Text)
    key_points: Mapped[list] = mapped_column(JSON, default=list)
    definitions: Mapped[list] = mapped_column(JSON, default=list)
    questions: Mapped[list] = mapped_column(JSON, default=list)
    segments_covered: Mapped[int] = mapped_column(Integer, default=0)
    provider: Mapped[str] = mapped_column(String(50), default="local")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LectureNote(Base):
    __tablename__ = "lecture_notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    lecture_id: Mapped[int] = mapped_column(ForeignKey("lectures.id"), index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    is_user_edited: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class UserPreference(Base):
    __tablename__ = "user_preferences"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    font_scale: Mapped[float] = mapped_column(Float, default=1.0)
    high_contrast: Mapped[bool] = mapped_column(default=False)
    caption_language: Mapped[str] = mapped_column(String(10), default="en")
    translation_language: Mapped[str] = mapped_column(String(10), default="hi")
    reading_level: Mapped[str] = mapped_column(String(20), default="high_school")
    tts_rate: Mapped[float] = mapped_column(Float, default=1.0)
    reduce_motion: Mapped[bool] = mapped_column(default=False)


# =============================================================================
# 3. PROFANITY MASKING  (English, Hindi, Hinglish - one implementation only)
# =============================================================================

ENGLISH_TERMS = ["fuck", "fucking", "fucker", "shit", "bullshit", "bitch", "bastard",
                 "asshole", "dick", "cunt", "slut", "whore", "motherfucker", "prick"]
HINDI_TERMS = ["गांडू", "भोसड़ी", "भोसडीके", "चूतिया", "मादरचोद", "बहनचोद", "रंडी", "हरामी", "कमीना"]
HINGLISH_TERMS = ["gandu", "gaandu", "bhosdi", "bhosdike", "bhosadike", "chutiya", "chutiye",
                  "madarchod", "behenchod", "bhenchod", "randi", "harami", "kamina",
                  "kaminey", "lauda", "lund", "saala", "saale"]
SAFE_WORDS = {"bass", "class", "classic", "assignment", "assess", "assembly", "pass",
              "passage", "analysis", "basic", "massive", "bcom", "msc", "lauki",
              "bhagwan", "dickens", "saalana"}

_TERMS = sorted(set(ENGLISH_TERMS + HINGLISH_TERMS + HINDI_TERMS), key=len, reverse=True)
_PATTERN = re.compile(
    r"(?<![\w\u0900-\u097F])(" + "|".join(re.escape(t) for t in _TERMS) + r")(?![\w\u0900-\u097F])",
    re.IGNORECASE,
)


def mask_text(text: str | None) -> str:
    """Keep the first letter, hide the rest: 'chutiya' -> 'c******'."""
    if not text:
        return ""

    def replace(match: re.Match) -> str:
        word = match.group(0)
        if word.lower() in SAFE_WORDS:
            return word
        return word[0] + "*" * (len(word) - 1) if len(word) > 1 else "*"

    return _PATTERN.sub(replace, text)


def contains_profanity(text: str) -> bool:
    return bool(text) and mask_text(text) != text


# =============================================================================
# 4. SECURITY
# =============================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
_ROUNDS = 180_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ROUNDS)
    return f"pbkdf2_sha256${_ROUNDS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, rounds, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, AttributeError):
        return False


def create_access_token(user_id: int) -> str:
    expire = utcnow() + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> int | None:
    try:
        return int(jwt.decode(token, SECRET_KEY, algorithms=["HS256"])["sub"])
    except (JWTError, KeyError, ValueError):
        return None


def current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    error = HTTPException(401, "Not authenticated", {"WWW-Authenticate": "Bearer"})
    if not token:
        raise error
    user_id = decode_token(token)
    if user_id is None:
        raise error
    user = db.get(User, user_id)
    if user is None:
        raise error
    return user


# =============================================================================
# 5. LIVE SESSION STATE  (interim captions + stale-result protection)
# =============================================================================

class LectureState:
    def __init__(self, lecture_id: int):
        self.lecture_id = lecture_id
        self.revision = 0
        self.interim_caption = ""
        self.interim_revision = 0
        self.finalised_ids: set[str] = set()
        self.summary_revision = 0
        self.segments_since_summary = 0
        self.listeners: set = set()

    def set_interim(self, text: str, revision: int | None = None) -> bool:
        """Replace the temporary caption. False means the packet was stale."""
        self.revision += 1
        rev = self.revision if revision is None else revision
        if rev < self.interim_revision:
            return False
        self.interim_caption = text
        self.interim_revision = rev
        return True

    def accept_final(self, client_segment_id: str, sequence_no: int) -> bool:
        """False means this segment was already stored (duplicate)."""
        if client_segment_id in self.finalised_ids:
            return False
        self.finalised_ids.add(client_segment_id)
        self.segments_since_summary += 1
        self.interim_caption = ""
        return True

    def should_summarise(self, batch_size: int) -> bool:
        return self.segments_since_summary >= batch_size

    def mark_summarised(self) -> int:
        self.segments_since_summary = 0
        self.summary_revision += 1
        return self.summary_revision

    def accept_summary(self, revision: int) -> bool:
        return revision >= self.summary_revision


class SessionManager:
    def __init__(self):
        self._states: dict[int, LectureState] = {}

    def state(self, lecture_id: int) -> LectureState:
        if lecture_id not in self._states:
            self._states[lecture_id] = LectureState(lecture_id)
        return self._states[lecture_id]

    async def connect(self, lecture_id: int, ws):
        self.state(lecture_id).listeners.add(ws)

    async def disconnect(self, lecture_id: int, ws):
        self.state(lecture_id).listeners.discard(ws)

    async def broadcast(self, lecture_id: int, message: dict):
        state = self.state(lecture_id)
        for ws in list(state.listeners):
            try:
                await ws.send_json(message)
            except Exception:
                state.listeners.discard(ws)


manager = SessionManager()


# =============================================================================
# 6. AI PROVIDERS  (adapters - swap a provider without touching the app)
# =============================================================================

STOPWORDS = {"the", "a", "an", "and", "or", "but", "if", "then", "so", "of", "to", "in",
             "on", "for", "with", "as", "is", "are", "was", "were", "be", "been", "it",
             "this", "that", "these", "those", "we", "you", "they", "he", "she", "i",
             "will", "can", "do", "does", "did", "not", "at", "by", "from", "about",
             "into", "over", "their", "our", "your", "its", "also", "very", "more",
             "there", "here", "now", "today", "what", "which", "when", "how", "why"}

LEVEL_SENTENCES = {"elementary": 2, "middle_school": 3, "high_school": 4, "academic": 6}

GLOSSARY = {
    ("en", "hi"): {"lecture": "व्याख्यान", "student": "विद्यार्थी", "teacher": "शिक्षक",
                   "today": "आज", "class": "कक्षा", "question": "प्रश्न", "answer": "उत्तर",
                   "water": "पानी", "energy": "ऊर्जा", "science": "विज्ञान", "book": "पुस्तक",
                   "example": "उदाहरण", "important": "महत्वपूर्ण", "chapter": "अध्याय",
                   "exam": "परीक्षा", "rain": "वर्षा", "sun": "सूर्य", "ground": "ज़मीन"},
    ("hi", "en"): {"व्याख्यान": "lecture", "विद्यार्थी": "student", "शिक्षक": "teacher",
                   "आज": "today", "कक्षा": "class", "पानी": "water", "वर्षा": "rain"},
}


def translate_text(text: str, source: str, target: str) -> str:
    """Offline glossary translation. Clearly labelled as sample output in the API."""
    if not text or source == target:
        return text
    table = GLOSSARY.get((source, target), {})
    if not table:
        return text
    return "".join(table.get(tok.lower(), tok) for tok in re.split(r"(\W+)", text))


def summarise_text(text: str, summary_type: str = "short", reading_level: str = "high_school") -> dict:
    """Extractive summary: picks the most informative sentences actually spoken.
    Nothing is invented, and it costs nothing."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?।])\s+", text) if s.strip()]
    if not sentences:
        return {"content": "", "key_points": [], "definitions": [], "questions": [], "provider": "local"}

    words = [w.lower() for w in re.findall(r"[\w\u0900-\u097F]+", text)]
    freq = Counter(w for w in words if w not in STOPWORDS and len(w) > 2)

    def score(sentence: str) -> float:
        tokens = [w.lower() for w in re.findall(r"[\w\u0900-\u097F]+", sentence)]
        return sum(freq.get(t, 0) for t in tokens) / (len(tokens) ** 0.5) if tokens else 0.0

    wanted = LEVEL_SENTENCES.get(reading_level, 4) * (2 if summary_type == "detailed" else 1)
    wanted = min(wanted, len(sentences))
    ranked = sorted(sentences, key=score, reverse=True)[:wanted]
    ordered = [s for s in sentences if s in ranked]

    if reading_level == "elementary":
        ordered = [re.split(r",| which | that | because ", s)[0].strip().rstrip(",") + "." for s in ordered]

    top_terms = [w for w, _ in freq.most_common(6)]

    def first_mention(term: str) -> str:
        for sentence in sentences:
            if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", sentence, re.IGNORECASE):
                return sentence.strip()
        return ""

    return {
        "content": " ".join(ordered),
        "key_points": ordered[: max(3, wanted // 2)],
        "definitions": [{"term": t, "meaning": first_mention(t)} for t in top_terms[:4]],
        "questions": [f"What was said about \u201c{t}\u201d in this lecture?" for t in top_terms[:3]],
        "provider": "local",
    }


def keywords_of(text: str, limit: int = 10) -> list[str]:
    words = [w.lower() for w in re.findall(r"[\w\u0900-\u097F]{3,}", text)]
    return [w for w, _ in Counter(w for w in words if w not in STOPWORDS).most_common(limit)]


# =============================================================================
# 7. SCHEMAS
# =============================================================================

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = ""
    role: str = "teacher"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    role: str


class LectureIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    source_language: str = "en"
    is_demo: bool = False


class LectureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    source_language: str
    status: str
    is_demo: bool
    created_at: datetime
    ended_at: datetime | None = None


class LectureStatusIn(BaseModel):
    status: str


class SegmentIn(BaseModel):
    client_segment_id: str = Field(min_length=1, max_length=64)
    sequence_no: int = Field(ge=0)
    text: str
    language: str = "en"
    start_ms: int = 0
    end_ms: int = 0
    confidence: float = 0.0
    is_final: bool = True


class SegmentOut(BaseModel):
    id: int
    client_segment_id: str
    sequence_no: int
    text: str
    language: str
    start_ms: int
    end_ms: int
    confidence: float
    translations: dict[str, str] = {}


class TranscriptOut(BaseModel):
    lecture_id: int
    count: int
    segments: list[SegmentOut]


class TranslateIn(BaseModel):
    target_language: str = "hi"
    segment_ids: list[int] | None = None


class TranslateOut(BaseModel):
    target_language: str
    provider: str
    translated_count: int
    is_sample_output: bool = False
    note: str = ""


class SummaryIn(BaseModel):
    summary_type: str = "short"
    reading_level: str = "high_school"
    force: bool = False


class SummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lecture_id: int
    summary_type: str
    reading_level: str
    content: str
    key_points: list = []
    definitions: list = []
    questions: list = []
    segments_covered: int
    provider: str
    created_at: datetime


class NoteIn(BaseModel):
    content: str


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lecture_id: int
    content: str
    keywords: list = []
    is_user_edited: bool
    updated_at: datetime


class PreferenceIn(BaseModel):
    font_scale: float = 1.0
    high_contrast: bool = False
    caption_language: str = "en"
    translation_language: str = "hi"
    reading_level: str = "high_school"
    tts_rate: float = 1.0
    reduce_motion: bool = False


class PreferenceOut(PreferenceIn):
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 8. ROUTES
# =============================================================================

router = APIRouter(prefix="/api/v1")


def owned_lecture(lecture_id: int, user: User, db: Session) -> Lecture:
    lecture = db.get(Lecture, lecture_id)
    if not lecture:
        raise HTTPException(404, "Lecture not found")
    if lecture.owner_id != user.id:
        raise HTTPException(403, "Not your lecture")
    return lecture


def segment_to_out(segment: TranscriptSegment) -> SegmentOut:
    """Student-facing shape: masked text only, never the raw original."""
    return SegmentOut(
        id=segment.id, client_segment_id=segment.client_segment_id,
        sequence_no=segment.sequence_no, text=segment.masked_text,
        language=segment.language, start_ms=segment.start_ms, end_ms=segment.end_ms,
        confidence=segment.confidence,
        translations={t.target_language: t.masked_text for t in segment.translations},
    )


# ---- auth and preferences ----

@router.post("/auth/register", response_model=TokenOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(409, "Email already registered")
    user = User(email=payload.email.lower(), full_name=payload.full_name,
                role=payload.role if payload.role in {"teacher", "student"} else "teacher",
                password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    db.add(UserPreference(user_id=user.id))
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id), user_id=user.id,
                    email=user.email, role=user.role)


@router.post("/auth/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return TokenOut(access_token=create_access_token(user.id), user_id=user.id,
                    email=user.email, role=user.role)


@router.get("/me/preferences", response_model=PreferenceOut)
def read_preferences(user: User = Depends(current_user), db: Session = Depends(get_db)):
    prefs = db.scalar(select(UserPreference).where(UserPreference.user_id == user.id))
    if not prefs:
        prefs = UserPreference(user_id=user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.put("/me/preferences", response_model=PreferenceOut)
def update_preferences(payload: PreferenceIn, user: User = Depends(current_user),
                       db: Session = Depends(get_db)):
    prefs = db.scalar(select(UserPreference).where(UserPreference.user_id == user.id))
    if not prefs:
        prefs = UserPreference(user_id=user.id)
        db.add(prefs)
    for field, value in payload.model_dump().items():
        setattr(prefs, field, value)
    db.commit()
    db.refresh(prefs)
    return prefs


# ---- lectures and transcript ----

@router.post("/lectures", response_model=LectureOut, status_code=201)
def create_lecture(payload: LectureIn, user: User = Depends(current_user),
                   db: Session = Depends(get_db)):
    lecture = Lecture(owner_id=user.id, title=payload.title,
                      source_language=payload.source_language, is_demo=payload.is_demo)
    db.add(lecture)
    db.commit()
    db.refresh(lecture)
    return lecture


@router.get("/lectures", response_model=list[LectureOut])
def list_lectures(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(Lecture).where(Lecture.owner_id == user.id)
                           .order_by(Lecture.id.desc())))


@router.get("/lectures/{lecture_id}", response_model=LectureOut)
def get_lecture(lecture_id: int, user: User = Depends(current_user),
                db: Session = Depends(get_db)):
    return owned_lecture(lecture_id, user, db)


@router.put("/lectures/{lecture_id}/status", response_model=LectureOut)
async def set_status(lecture_id: int, payload: LectureStatusIn,
                     user: User = Depends(current_user), db: Session = Depends(get_db)):
    if payload.status not in {"created", "live", "paused", "processing", "completed"}:
        raise HTTPException(422, "Unknown status")
    lecture = owned_lecture(lecture_id, user, db)
    lecture.status = payload.status
    if payload.status == "completed":
        lecture.ended_at = utcnow()
    db.commit()
    db.refresh(lecture)
    await manager.broadcast(lecture_id, {"type": "lecture_status", "status": lecture.status})
    return lecture


@router.post("/lectures/{lecture_id}/segments", response_model=SegmentOut)
async def add_segment(lecture_id: int, payload: SegmentIn,
                      user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Store ONE finalised segment.
    Interim text is rejected; the same client_segment_id is stored exactly once."""
    lecture = owned_lecture(lecture_id, user, db)
    if not payload.is_final:
        raise HTTPException(400, "Interim results are not stored. Send them over the WebSocket.")
    if not payload.text.strip():
        raise HTTPException(400, "Empty segment")

    existing = db.scalar(select(TranscriptSegment).where(
        TranscriptSegment.lecture_id == lecture.id,
        TranscriptSegment.client_segment_id == payload.client_segment_id))
    if existing:
        return segment_to_out(existing)

    segment = TranscriptSegment(
        lecture_id=lecture.id, client_segment_id=payload.client_segment_id,
        sequence_no=payload.sequence_no, text=payload.text.strip(),
        masked_text=mask_text(payload.text.strip()),
        language=payload.language or lecture.source_language,
        start_ms=payload.start_ms, end_ms=payload.end_ms, confidence=payload.confidence)
    db.add(segment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(TranscriptSegment).where(
            TranscriptSegment.lecture_id == lecture.id,
            TranscriptSegment.client_segment_id == payload.client_segment_id))
        if existing:
            return segment_to_out(existing)
        raise HTTPException(409, "Duplicate sequence number") from None

    db.refresh(segment)
    manager.state(lecture.id).accept_final(segment.client_segment_id, segment.sequence_no)
    out = segment_to_out(segment)
    await manager.broadcast(lecture.id, {"type": "final_segment", "segment": out.model_dump()})
    return out


@router.get("/lectures/{lecture_id}/transcript", response_model=TranscriptOut)
def get_transcript(lecture_id: int, q: str | None = Query(None),
                   user: User = Depends(current_user), db: Session = Depends(get_db)):
    lecture = owned_lecture(lecture_id, user, db)
    stmt = (select(TranscriptSegment).where(TranscriptSegment.lecture_id == lecture.id)
            .order_by(TranscriptSegment.sequence_no))
    if q:
        # Search the masked text, so a search can never reveal a masked word.
        stmt = stmt.where(TranscriptSegment.masked_text.ilike(f"%{q}%"))
    segments = list(db.scalars(stmt))
    return TranscriptOut(lecture_id=lecture.id, count=len(segments),
                         segments=[segment_to_out(s) for s in segments])


# ---- translation, summaries, notes ----

@router.post("/lectures/{lecture_id}/translate", response_model=TranslateOut)
async def translate_lecture(lecture_id: int, payload: TranslateIn,
                            user: User = Depends(current_user), db: Session = Depends(get_db)):
    lecture = owned_lecture(lecture_id, user, db)
    stmt = select(TranscriptSegment).where(TranscriptSegment.lecture_id == lecture.id)
    if payload.segment_ids:
        stmt = stmt.where(TranscriptSegment.id.in_(payload.segment_ids))
    segments = list(db.scalars(stmt.order_by(TranscriptSegment.sequence_no)))

    done = 0
    for segment in segments:
        if segment.language == payload.target_language:
            continue
        if db.scalar(select(Translation).where(
                Translation.segment_id == segment.id,
                Translation.target_language == payload.target_language)):
            continue
        translated = translate_text(segment.text, segment.language, payload.target_language)
        db.add(Translation(segment_id=segment.id, target_language=payload.target_language,
                           text=translated, masked_text=mask_text(translated),
                           provider=TRANSLATION_PROVIDER))
        done += 1
    db.commit()

    is_sample = TRANSLATION_PROVIDER == "local"
    await manager.broadcast(lecture.id, {"type": "translation_ready",
                                         "language": payload.target_language, "count": done})
    return TranslateOut(
        target_language=payload.target_language, provider=TRANSLATION_PROVIDER,
        translated_count=done, is_sample_output=is_sample,
        note=("Offline sample translation from a small built-in glossary - not production "
              "translation quality. Set TRANSLATION_PROVIDER to a real engine." if is_sample else ""))


@router.post("/lectures/{lecture_id}/summarize", response_model=SummaryOut)
async def summarize_lecture(lecture_id: int, payload: SummaryIn,
                            user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Summaries are built from FINALISED segments only, in batches."""
    lecture = owned_lecture(lecture_id, user, db)
    segments = list(db.scalars(select(TranscriptSegment)
                               .where(TranscriptSegment.lecture_id == lecture.id)
                               .order_by(TranscriptSegment.sequence_no)))
    if not segments:
        raise HTTPException(400, "Nothing finalised yet to summarise")

    state = manager.state(lecture.id)
    if not payload.force and not state.should_summarise(SUMMARY_DEBOUNCE_SEGMENTS):
        latest = db.scalar(select(Summary).where(
            Summary.lecture_id == lecture.id,
            Summary.summary_type == payload.summary_type,
            Summary.reading_level == payload.reading_level).order_by(Summary.id.desc()))
        if latest:
            return latest

    revision_at_start = state.summary_revision
    result = summarise_text(" ".join(s.text for s in segments),
                            payload.summary_type, payload.reading_level)

    if not state.accept_summary(revision_at_start):
        # A newer summary landed while this one was being generated. Drop this one.
        latest = db.scalar(select(Summary).where(Summary.lecture_id == lecture.id)
                           .order_by(Summary.id.desc()))
        if latest:
            return latest

    summary = Summary(
        lecture_id=lecture.id, summary_type=payload.summary_type,
        reading_level=payload.reading_level, content=mask_text(result["content"]),
        key_points=[mask_text(p) for p in result["key_points"]],
        definitions=[{"term": mask_text(d["term"]), "meaning": mask_text(d["meaning"])}
                     for d in result["definitions"]],
        questions=[mask_text(q) for q in result["questions"]],
        segments_covered=len(segments), provider=result["provider"])
    db.add(summary)
    db.commit()
    db.refresh(summary)
    state.mark_summarised()
    await manager.broadcast(lecture.id, {"type": "summary_ready", "summary_id": summary.id})
    return summary


@router.get("/lectures/{lecture_id}/summaries", response_model=list[SummaryOut])
def list_summaries(lecture_id: int, user: User = Depends(current_user),
                   db: Session = Depends(get_db)):
    lecture = owned_lecture(lecture_id, user, db)
    return list(db.scalars(select(Summary).where(Summary.lecture_id == lecture.id)
                           .order_by(Summary.id.desc())))


@router.get("/lectures/{lecture_id}/notes", response_model=NoteOut)
def get_notes(lecture_id: int, user: User = Depends(current_user),
              db: Session = Depends(get_db)):
    lecture = owned_lecture(lecture_id, user, db)
    note = db.scalar(select(LectureNote).where(LectureNote.lecture_id == lecture.id)
                     .order_by(LectureNote.id.desc()))
    if note:
        return note
    segments = list(db.scalars(select(TranscriptSegment)
                               .where(TranscriptSegment.lecture_id == lecture.id)
                               .order_by(TranscriptSegment.sequence_no)))
    text = " ".join(s.text for s in segments)
    draft = summarise_text(text) if text else None
    note = LectureNote(
        lecture_id=lecture.id,
        content=mask_text("\n".join(f"\u2022 {p}" for p in draft["key_points"])) if draft else "",
        keywords=keywords_of(mask_text(text)) if text else [], is_user_edited=False)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.put("/lectures/{lecture_id}/notes", response_model=NoteOut)
def save_notes(lecture_id: int, payload: NoteIn, user: User = Depends(current_user),
               db: Session = Depends(get_db)):
    lecture = owned_lecture(lecture_id, user, db)
    note = db.scalar(select(LectureNote).where(LectureNote.lecture_id == lecture.id)
                     .order_by(LectureNote.id.desc()))
    if not note:
        note = LectureNote(lecture_id=lecture.id)
        db.add(note)
    note.content = mask_text(payload.content)
    note.keywords = keywords_of(note.content)
    note.is_user_edited = True
    db.commit()
    db.refresh(note)
    return note


# ---- exports and audio upload ----

def srt_time(ms: int) -> str:
    hours, rem = divmod(max(ms, 0), 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def text_for(segment: TranscriptSegment, language: str | None) -> str:
    if not language or language == segment.language:
        return segment.masked_text
    for translation in segment.translations:
        if translation.target_language == language:
            return translation.masked_text
    return segment.masked_text


@router.get("/lectures/{lecture_id}/export")
def export_transcript(lecture_id: int, format: str = Query("txt", pattern="^(txt|srt|csv)$"),
                      language: str | None = Query(None), user: User = Depends(current_user),
                      db: Session = Depends(get_db)):
    """Exports are built from the MASKED text, exactly like the on-screen transcript."""
    lecture = owned_lecture(lecture_id, user, db)
    segments = list(db.scalars(select(TranscriptSegment)
                               .where(TranscriptSegment.lecture_id == lecture.id)
                               .order_by(TranscriptSegment.sequence_no)))
    safe_title = "".join(c if c.isalnum() or c in "-_ " else "_" for c in lecture.title).strip()
    filename = f"{safe_title or 'lecture'}-{lecture.id}.{format}"

    if format == "txt":
        lines = [lecture.title, "=" * len(lecture.title), ""]
        lines += [f"[{srt_time(s.start_ms).split(',')[0]}] {text_for(s, language)}" for s in segments]
        body, media = "\n".join(lines), "text/plain; charset=utf-8"
    elif format == "srt":
        blocks = []
        for index, s in enumerate(segments, start=1):
            end = s.end_ms if s.end_ms > s.start_ms else s.start_ms + 2000
            blocks.append(f"{index}\n{srt_time(s.start_ms)} --> {srt_time(end)}\n{text_for(s, language)}\n")
        body, media = "\n".join(blocks), "application/x-subrip; charset=utf-8"
    else:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["sequence", "start_ms", "end_ms", "language", "text", "confidence"])
        for s in segments:
            writer.writerow([s.sequence_no, s.start_ms, s.end_ms, language or s.language,
                             text_for(s, language), round(s.confidence, 3)])
        body, media = buffer.getvalue(), "text/csv; charset=utf-8"

    return StreamingResponse(io.BytesIO(body.encode("utf-8")), media_type=media,
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})


ALLOWED_AUDIO = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/webm",
                 "audio/ogg", "audio/mp4", "audio/m4a", "audio/x-m4a"}


@router.post("/lectures/{lecture_id}/audio", status_code=201)
async def upload_audio(lecture_id: int, file: UploadFile = File(...),
                       user: User = Depends(current_user), db: Session = Depends(get_db)):
    lecture = owned_lecture(lecture_id, user, db)
    if file.content_type not in ALLOWED_AUDIO:
        raise HTTPException(415, f"Unsupported audio type: {file.content_type}")
    data = await file.read()
    if len(data) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(413, f"File larger than {MAX_AUDIO_MB} MB")

    os.makedirs(AUDIO_DIR, exist_ok=True)
    extension = os.path.splitext(file.filename or "")[1][:10]
    path = os.path.join(AUDIO_DIR, f"{uuid.uuid4().hex}{extension}")
    with open(path, "wb") as handle:
        handle.write(data)

    record = AudioFile(lecture_id=lecture.id, original_filename=file.filename or "audio",
                       storage_path=path, content_type=file.content_type,
                       size_bytes=len(data), status="uploaded")
    db.add(record)
    lecture.status = "processing"
    db.commit()
    db.refresh(record)
    return {"audio_id": record.id, "status": record.status, "size_bytes": record.size_bytes,
            "next_step": "Stored. Transcribing uploaded files needs a real speech engine; "
                         "live microphone captions work without one."}


# ---- demo mode (clearly labelled sample content) ----

SAMPLE_SENTENCES = [
    "Good morning everyone, today we will study the water cycle and why it matters.",
    "Water on the earth's surface is heated by the sun and turns into vapour. This is called evaporation.",
    "The vapour rises, cools down at a higher altitude, and forms tiny droplets. That process is condensation.",
    "When the droplets become heavy enough they fall back as rain, snow or hail. We call this precipitation.",
    "Some of that water soaks into the ground and recharges the groundwater table.",
    "The rest flows into rivers and finally into the sea, and the whole cycle starts again.",
    "For the exam, remember the four stages in order: evaporation, condensation, precipitation and collection.",
]


@router.post("/demo/lecture", status_code=201)
def create_demo_lecture(user: User = Depends(current_user), db: Session = Depends(get_db)):
    lecture = Lecture(owner_id=user.id, title="Sample lecture - The Water Cycle (demo)",
                      source_language="en", status="completed", is_demo=True)
    db.add(lecture)
    db.flush()
    start = 0
    for index, sentence in enumerate(SAMPLE_SENTENCES):
        db.add(TranscriptSegment(
            lecture_id=lecture.id, client_segment_id=f"demo-{lecture.id}-{index}",
            sequence_no=index, text=sentence, masked_text=mask_text(sentence),
            language="en", start_ms=start, end_ms=start + 6000, confidence=0.95))
        start += 6500
    db.commit()
    db.refresh(lecture)
    return {"lecture_id": lecture.id, "is_demo": True, "segments": len(SAMPLE_SENTENCES),
            "notice": "Sample content for demonstration - not produced by live speech recognition."}


# =============================================================================
# 9. APPLICATION
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    yield


app = FastAPI(title="AccessLearn AI", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.websocket("/ws/lectures/{lecture_id}/live")
async def live_lecture(websocket: WebSocket, lecture_id: int, token: str = ""):
    """Interim captions travel over this socket and are never written to the database."""
    if not token or decode_token(token) is None:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    await manager.connect(lecture_id, websocket)
    state = manager.state(lecture_id)
    await websocket.send_json({"type": "connected", "lecture_id": lecture_id})
    try:
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "interim":
                if state.set_interim(message.get("text", ""), message.get("revision")):
                    await manager.broadcast(lecture_id, {
                        "type": "interim_caption",
                        "text": mask_text(state.interim_caption),
                        "revision": state.interim_revision})
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(lecture_id, websocket)


@app.get("/health")
def health():
    return {"status": "ok", "app": "AccessLearn AI",
            "providers": {"asr": ASR_PROVIDER, "translation": TRANSLATION_PROVIDER,
                          "llm": LLM_PROVIDER},
            "profanity_masking": True}


@app.get("/", include_in_schema=False)
def index():
    path = os.path.join(BASE_DIR, "index.html")
    if not os.path.exists(path):
        raise HTTPException(500, "index.html is missing - keep it next to app.py")
    return FileResponse(path)


if __name__ == "__main__":
    import uvicorn

    print("AccessLearn AI -> http://127.0.0.1:8000   (use Chrome or Edge for live captions)")
    uvicorn.run(app, host="127.0.0.1", port=8000)
