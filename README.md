# AccessLearn AI

> Inclusive classroom learning: live captions, simple summaries and notes for every student.

AccessLearn AI helps students follow class lectures and learn from them afterwards. It turns the teacher's speech into live captions and gives a short summary at the reading level each student chooses, with bigger text, high contrast, important terms, read-aloud, translation and downloadable notes. It was designed with deaf and hard-of-hearing students in mind, and it helps any student who misses a point, wants to revise, or finds the language of the lecture hard to follow.

## The Problem

Every classroom has students who miss something: a student who cannot hear well, a student who lost focus for a minute, a student whose first language is different from the language of the lecture, or a student who finds the language hard to follow. Not every classroom has real-time captions or easy-to-read notes, and professional tools can be costly or hard to set up. AccessLearn AI gives every student a free, simple way to follow the lecture and revise from it later.

## Who Is It For?

- **Deaf and hard-of-hearing students:** live captions, bigger text and high contrast
- **Students who missed something:** a saved, searchable transcript of the lecture
- **Students revising later:** short summaries, key points, questions to revise and downloadable notes
- **Students whose first language is different:** captions in English or Hindi, and English to Hindi translation
- **Students who find the language hard to follow:** summaries at a simpler reading level, read-aloud with adjustable speed, and larger text

## Features

- **Live captions** from speech, using the browser's built-in speech recognition (English India, English US, Hindi)
- **Live caption updates** over WebSockets while the lecture is running
- **Lecture transcripts** saved for every lecture, with a search box
- **Summaries at your reading level**: Elementary, Middle school, High school or Academic, in Short or Detailed form, with key points, important terms and questions to revise. Summaries are built from sentences that were actually spoken, so nothing is invented.
- **Translation** between English and Hindi (basic offline glossary for demo purposes)
- **Read-aloud** with adjustable speed (browser text-to-speech)
- **Accessibility settings**: adjustable text size, high contrast mode, reduce motion, skip-to-content link, and live captions that screen readers can announce
- **Keyboard shortcuts**: Alt+R start/stop recording, Alt+S summary, Alt+P read aloud, Esc to stop reading
- **Notes** for each lecture, with automatically extracted keywords
- **Export** transcripts as TXT, SRT (subtitles) or CSV
- **Audio upload** (MP3, WAV, WebM, OGG, M4A, up to 100 MB by default). The file is stored; transcribing uploaded audio is not supported yet.
- **Profanity masking** in English, Hindi and Hinglish
- **User accounts** with password hashing and JWT login, saved accessibility preferences, and a one-click sample lecture

## Tech Stack

| Part | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Database | SQLite with SQLAlchemy |
| Auth | JWT (python-jose), salted PBKDF2 password hashing |
| Real-time | WebSockets |
| Frontend | HTML, CSS, JavaScript (single file, no external libraries) |
| Speech to text | Browser Web Speech API (SpeechRecognition) |
| Text to speech | Browser Web Speech API (SpeechSynthesis) |
| Summaries | Local extractive summarizer (no paid API) |

No paid or external API keys are needed.

## How to Run

1. Make sure Python 3.10 or newer is installed.
2. Clone this repository:
   ```
   git clone https://github.com/ridhigarg1122-coder/AccessLearn-AI.git
   cd AccessLearn-AI
   ```
3. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
4. Start the app:
   ```
   python app.py
   ```
5. Open **http://127.0.0.1:8000** in **Chrome or Edge** (live captions need their speech recognition).
6. Create an account, then click **Load sample lecture** to try it quickly, or create your own lecture and press Start recording.

Keep `index.html` in the same folder as `app.py`. The database file and audio folder are created automatically on the first run. Interactive API docs are available at `/docs` while the app runs.

## Configuration (optional)

Everything has a working default. To change a setting, use an environment variable:

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Signs login tokens. **Change this before deploying.** | placeholder value |
| `DATABASE_URL` | Database location | `sqlite:///./accesslearn.db` |
| `ACCESS_TOKEN_MINUTES` | Login session length | `720` |
| `AUDIO_STORAGE_DIR` | Where uploaded audio is stored | `./audio_store` |
| `MAX_AUDIO_MB` | Max audio upload size | `100` |

## Project Structure

```
AccessLearn-AI/
├── app.py             # FastAPI backend (API, database, auth, WebSocket)
├── index.html         # Frontend web app
├── requirements.txt   # Python dependencies
└── README.md
```

## Main API Endpoints

| Method | Endpoint | What it does |
|---|---|---|
| POST | `/api/v1/auth/register` | Create an account |
| POST | `/api/v1/auth/login` | Log in |
| GET / PUT | `/api/v1/me/preferences` | Read or save accessibility preferences |
| POST / GET | `/api/v1/lectures` | Create or list lectures |
| GET | `/api/v1/lectures/{id}/transcript` | Get or search a transcript |
| POST | `/api/v1/lectures/{id}/translate` | Translate a transcript |
| POST | `/api/v1/lectures/{id}/summarize` | Generate a summary |
| GET / PUT | `/api/v1/lectures/{id}/notes` | Read or save notes |
| GET | `/api/v1/lectures/{id}/export` | Export as txt, srt or csv |
| POST | `/api/v1/lectures/{id}/audio` | Upload recorded audio |
| POST | `/api/v1/demo/lecture` | Create a sample lecture |
| WS | `/ws/lectures/{id}/live` | Live captions |

## Limitations

- Live captions use the browser's speech recognition. It works best in Chrome and Edge, needs an internet connection, and can be less accurate with strong accents or noisy rooms.
- Summaries and important terms work best for lectures spoken in English. Hindi or Hinglish speech can produce common words as "important terms".
- Translation works only between English and Hindi, using a small offline glossary. It is a demo, not full machine translation.
- Uploaded audio files are stored but not transcribed yet.

## Screenshots

**Login**

<img width="1470" height="841" alt="Screenshot 2026-11-12 142737" src="https://github.com/user-attachments/assets/f19dd14d-1c3c-4e5b-9442-b08f836bab16" />


**Your lectures**

<img width="1903" height="915" alt="Screenshot 2026-11-12 143042" src="https://github.com/user-attachments/assets/c4083c6b-6634-45f3-9a9d-b6ea9473dc82" />


**Lecture page**

<img width="1883" height="902" alt="Screenshot 2026-11-12 143253" src="https://github.com/user-attachments/assets/3440109f-49bb-4ddf-abca-ccae575bbe95" />


**Accessibility settings**

<img width="1893" height="913" alt="Screenshot 2026-11-12 143405" src="https://github.com/user-attachments/assets/c37f7471-a302-4ad1-8810-b00765a89a13" />


**Live transcript**

<img width="1885" height="903" alt="Screenshot 2026-11-12 145651" src="https://github.com/user-attachments/assets/3b448713-5cbd-4c05-8aef-17551fa9353d" />

**Summary**

<img width="767" height="833" alt="Screenshot 2026-11-12 150757" src="https://github.com/user-attachments/assets/c104c0f7-6746-44c7-a743-2f0405b6a03d" />



## Future Improvements

- Better accuracy for Indian accents using a dedicated speech model
- Transcription of uploaded audio files
- Better important terms for Hindi and Hinglish lectures
- Full translation, with more Indian languages
- Optional AI-generated summaries
- Mobile-friendly layout

## Team

- Ridhi Garg (leader)
- Krishna Sharma
- Shivam
- Ehshanul Hooda

## Why We Built This

Learning should not depend on how well you can hear or how well you know the language. AccessLearn AI gives every student live captions, simple summaries, translation and notes they can revise from, for free.
