# AccessLearn-AI
AccessLearn AI helps deaf and hard-of-hearing students follow class lectures. It turns the teacher’s speech into live captions and gives a short summary at the reading level each student chooses, with bigger text, high contrast, word meanings, read-aloud and downloadable notes.
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AccessLearn AI - Accessible Classroom Learning</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500;600;700&display=swap');
    
    body {
      font-family: 'Lexend', sans-serif;
      transition: background-color 0.3s, color 0.3s;
    }

    /* High Contrast Mode */
    body.high-contrast {
      background-color: #000000 !important;
      color: #FFFF00 !important;
    }
    .high-contrast .hc-card {
      background-color: #000000 !important;
      border: 2px solid #FFFF00 !important;
      color: #FFFF00 !important;
    }
    .high-contrast .hc-text {
      color: #FFFF00 !important;
    }
    .high-contrast .hc-btn {
      background-color: #FFFF00 !important;
      color: #000000 !important;
      border: 2px solid #FFFFFF !important;
      font-weight: bold !important;
    }
    .high-contrast .hc-input {
      background-color: #000000 !important;
      color: #FFFF00 !important;
      border: 2px solid #FFFF00 !important;
    }
    .high-contrast .hc-badge {
      background-color: #FFFF00 !important;
      color: #000000 !important;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }
    ::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.05);
      border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb {
      background: rgba(100, 116, 139, 0.3);
      border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: rgba(100, 116, 139, 0.5);
    }

    /* Pulse animation for live audio */
    @keyframes bar-pulse {
      0%, 100% { height: 6px; }
      50% { height: 28px; }
    }
    .animate-bar-1 { animation: bar-pulse 1s infinite ease-in-out; }
    .animate-bar-2 { animation: bar-pulse 1.2s infinite ease-in-out 0.2s; }
    .animate-bar-3 { animation: bar-pulse 0.8s infinite ease-in-out 0.4s; }
    .animate-bar-4 { animation: bar-pulse 1.1s infinite ease-in-out 0.1s; }
    .animate-bar-5 { animation: bar-pulse 0.9s infinite ease-in-out 0.3s; }

    .highlight-search {
      background-color: #fef08a;
      color: #854d0e;
      padding: 0 4px;
      border-radius: 2px;
    }
    .high-contrast .highlight-search {
      background-color: #ffffff;
      color: #000000;
    }

    .tooltip-term {
      border-bottom: 2px dashed #6366f1;
      cursor: help;
      position: relative;
    }
    .high-contrast .tooltip-term {
      border-bottom: 2px dashed #FFFF00;
    }
  </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen flex flex-col">

  <!-- Navigation / Header -->
  <header class="bg-indigo-700 text-white shadow-md sticky top-0 z-50 hc-card">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap justify-between items-center gap-4">
      <div class="flex items-center space-x-3">
        <div class="p-2 bg-white/10 rounded-lg backdrop-blur-sm">
          <i class="fa-solid fa-graduation-cap text-2xl text-indigo-200 hc-text"></i>
        </div>
        <div>
          <h1 class="text-xl font-bold tracking-tight flex items-center gap-2">
            AccessLearn AI
            <span class="text-xs font-normal bg-indigo-500 text-indigo-100 px-2 py-0.5 rounded-full hc-badge">v1.0 Prototype</span>
          </h1>
          <p class="text-xs text-indigo-200 hc-text">Accessible Classroom Learning & Adaptive Transcripts</p>
        </div>
      </div>

      <!-- Quick Accessibility Toolbar -->
      <div class="flex items-center space-x-2 bg-indigo-800/60 p-1.5 rounded-xl border border-indigo-500/30 hc-card">
        <!-- Font Size Adjuster -->
        <div class="flex items-center space-x-1 px-2 border-r border-indigo-600">
          <span class="text-xs font-medium mr-1 text-indigo-200 hc-text"><i class="fa-solid fa-text-height mr-1"></i> Text:</span>
          <button id="btn-font-sm" onclick="setFontSize('sm')" class="w-7 h-7 rounded text-xs font-bold bg-indigo-700 hover:bg-indigo-600 focus:ring-2 focus:ring-white transition hc-btn">A-</button>
          <button id="btn-font-md" onclick="setFontSize('md')" class="w-7 h-7 rounded text-xs font-bold bg-indigo-500 hover:bg-indigo-600 focus:ring-2 focus:ring-white transition hc-btn">A</button>
          <button id="btn-font-lg" onclick="setFontSize('lg')" class="w-7 h-7 rounded text-sm font-bold bg-indigo-700 hover:bg-indigo-600 focus:ring-2 focus:ring-white transition hc-btn">A+</button>
        </div>

        <!-- High Contrast Mode Toggle -->
        <button id="toggle-contrast" onclick="toggleHighContrast()" class="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition hc-btn">
          <i class="fa-solid fa-[#FFFF00] fa-circle-half-stroke"></i>
          <span id="contrast-label">High Contrast</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Main Content Layout -->
  <main class="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">

    <!-- LEFT COLUMN: Input Controls & Live Captions (5 Cols) -->
    <section class="lg:col-span-5 flex flex-col gap-6">

      <!-- Live Speech & Demo Controls -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 hc-card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-semibold text-slate-800 flex items-center gap-2 hc-text">
            <i class="fa-solid fa-microphone-lines text-indigo-600 hc-text"></i>
            Lecture Audio Studio
          </h2>
          <span id="status-badge" class="px-2.5 py-1 text-xs rounded-full font-medium bg-slate-100 text-slate-600 hc-badge">
            <i class="fa-solid fa-circle text-[8px] mr-1 text-slate-400"></i> Standby
          </span>
        </div>

        <!-- Audio Control Buttons -->
        <div class="grid grid-cols-2 gap-3 mb-4">
          <button id="btn-mic-toggle" onclick="toggleMic()" class="flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm transition hc-btn">
            <i class="fa-solid fa-microphone" id="mic-icon"></i>
            <span id="mic-text">Start Mic</span>
          </button>

          <button id="btn-demo-toggle" onclick="toggleDemoSimulation()" class="flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-sm font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition hc-btn">
            <i class="fa-solid fa-play" id="demo-icon"></i>
            <span id="demo-text">Simulate Demo</span>
          </button>
        </div>

        <!-- Audio Wave Visualizer Animation -->
        <div id="audio-visualizer" class="h-10 bg-slate-900 rounded-xl flex items-center justify-center gap-1.5 px-4 opacity-50 transition-opacity">
          <span class="w-1 bg-emerald-400 rounded-full h-1.5 transition-all"></span>
          <span class="w-1 bg-emerald-400 rounded-full h-1.5 transition-all"></span>
          <span class="w-1 bg-emerald-400 rounded-full h-1.5 transition-all"></span>
          <span class="w-1 bg-emerald-400 rounded-full h-1.5 transition-all"></span>
          <span class="w-1 bg-emerald-400 rounded-full h-1.5 transition-all"></span>
          <span class="text-xs text-slate-400 font-mono ml-2">Audio Inactive</span>
        </div>
      </div>

      <!-- Live Real-Time Captions Box -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex-grow flex flex-col hc-card">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-base font-semibold text-slate-800 flex items-center gap-2 hc-text">
            <i class="fa-solid fa-closed-captioning text-indigo-600 hc-text"></i>
            Live Accessible Captions
          </h2>
          <button onclick="clearCaptions()" class="text-xs text-slate-400 hover:text-rose-500 transition hc-text">
            <i class="fa-solid fa-trash-can mr-1"></i>Clear
          </button>
        </div>

        <!-- Captions Text Window -->
        <div id="caption-window" class="flex-grow min-h-[220px] max-h-[320px] overflow-y-auto bg-slate-900 text-slate-100 p-4 rounded-xl font-medium leading-relaxed shadow-inner border border-slate-800 hc-card">
          <p id="caption-placeholder" class="text-slate-500 italic text-sm">
            Live captions will scroll here in real-time as the lecture progresses. Start your microphone or run the demo lecture to preview.
          </p>
          <div id="caption-stream" class="space-y-3 font-caption text-base"></div>
        </div>
      </div>

      <!-- Quick Index & Topic Keywords -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 hc-card">
        <h3 class="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2 hc-text">
          <i class="fa-solid fa-tags text-indigo-500"></i> Filter Topics & Keywords
        </h3>
        <div class="flex flex-wrap gap-2" id="topic-tags">
          <button onclick="filterByTag('all')" class="px-3 py-1 rounded-lg text-xs font-medium bg-indigo-100 text-indigo-700 hover:bg-indigo-200 transition hc-badge">All Topics</button>
          <button onclick="filterByTag('photosynthesis')" class="px-3 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition hc-badge">#Photosynthesis</button>
          <button onclick="filterByTag('chloroplast')" class="px-3 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition hc-badge">#Chloroplast</button>
          <button onclick="filterByTag('atp')" class="px-3 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition hc-badge">#ATP & Energy</button>
          <button onclick="filterByTag('calvin')" class="px-3 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition hc-badge">#Calvin Cycle</button>
        </div>
      </div>

    </section>

    <!-- RIGHT COLUMN: Adaptive Notes, Summaries & Translation (7 Cols) -->
    <section class="lg:col-span-7 flex flex-col gap-6">

      <!-- Navigation Tabs -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-2 flex space-x-2 hc-card">
        <button id="tab-btn-summary" onclick="switchTab('summary')" class="flex-1 py-2 px-3 rounded-xl text-xs sm:text-sm font-semibold transition bg-indigo-600 text-white hc-btn">
          <i class="fa-solid fa-sliders mr-1.5"></i>Adaptive Summary
        </button>
        <button id="tab-btn-notes" onclick="switchTab('notes')" class="flex-1 py-2 px-3 rounded-xl text-xs sm:text-sm font-semibold transition text-slate-600 hover:bg-slate-100 hc-btn">
          <i class="fa-solid fa-list-check mr-1.5"></i>Searchable Transcript
        </button>
        <button id="tab-btn-translate" onclick="switchTab('translate')" class="flex-1 py-2 px-3 rounded-xl text-xs sm:text-sm font-semibold transition text-slate-600 hover:bg-slate-100 hc-btn">
          <i class="fa-solid fa-language mr-1.5"></i>Multilingual TTS
        </button>
      </div>

      <!-- TAB 1: Adaptive Reading Levels & Summarization -->
      <div id="tab-content-summary" class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 flex flex-col gap-5 hc-card">
        <div>
          <div class="flex justify-between items-center mb-2">
            <h2 class="text-base font-semibold text-slate-800 hc-text">
              <i class="fa-solid fa-layer-group text-indigo-600 mr-1.5"></i>
              Adjustable Reading Complexity Level
            </h2>
            <span id="level-indicator" class="text-xs font-bold px-3 py-1 rounded-full bg-indigo-100 text-indigo-800 hc-badge">
              Elementary (Grades 1-5)
            </span>
          </div>
          <p class="text-xs text-slate-500 mb-4 hc-text">
            Slide to adapt vocabulary, sentence length, and structural complexity for diverse neurodiverse or language learners.
          </p>

          <!-- Range Slider for Reading Level -->
          <div class="space-y-2 bg-slate-50 p-4 rounded-xl border border-slate-200 hc-card">
            <input type="range" id="reading-level-range" min="1" max="4" step="1" value="1" oninput="updateReadingLevel(this.value)" class="w-full accent-indigo-600 cursor-pointer">
            <div class="flex justify-between text-[11px] font-semibold text-slate-500 hc-text">
              <span>1: Elementary</span>
              <span>2: Middle School</span>
              <span>3: High School</span>
              <span>4: Academic / Expert</span>
            </div>
          </div>
        </div>

        <hr class="border-slate-100">

        <!-- Generated Adaptive Summary View -->
        <div>
          <h3 class="text-sm font-semibold text-slate-700 mb-2 flex items-center justify-between hc-text">
            <span>Simplified Concept Breakdown</span>
            <span class="text-xs font-normal text-slate-400"><i class="fa-solid fa-lightbulb text-amber-500 mr-1"></i>Hover highlighted terms for definitions</span>
          </h3>
          
          <div id="summary-display" class="bg-indigo-50/50 rounded-xl p-4 text-slate-800 leading-relaxed text-sm border border-indigo-100/80 space-y-3 hc-card">
            <!-- Dynamic Content Injected Here -->
          </div>
        </div>

        <!-- Key Takeaway Bullets -->
        <div class="space-y-2">
          <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider hc-text">Key Core Takeaways</h4>
          <ul id="summary-bullets" class="space-y-2 text-xs sm:text-sm text-slate-700 hc-text">
            <!-- Dynamic Bullets -->
          </ul>
        </div>
      </div>

      <!-- TAB 2: Searchable Timestamped Notes & Transcript -->
      <div id="tab-content-notes" class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 hidden flex-col gap-4 hc-card">
        
        <!-- Search Bar -->
        <div class="relative">
          <i class="fa-solid fa-magnifying-glass absolute left-3.5 top-3 text-slate-400"></i>
          <input type="text" id="transcript-search" oninput="handleSearch(this.value)" placeholder="Search keywords (e.g., 'sunlight', 'chlorophyll', 'oxygen')..." class="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 hc-input">
        </div>

        <!-- Filter Count Header -->
        <div class="flex justify-between items-center text-xs text-slate-500 px-1 hc-text">
          <span id="search-result-count">Showing all timestamps</span>
          <button onclick="exportTranscript('txt')" class="text-indigo-600 font-semibold hover:underline flex items-center gap-1">
            <i class="fa-solid fa-download"></i> Export Markdown/Text
          </button>
        </div>

        <!-- Transcript Feed -->
        <div id="full-transcript-list" class="space-y-3 max-h-[420px] overflow-y-auto pr-1">
          <!-- Transcripts Injected Dynamically -->
        </div>
      </div>

      <!-- TAB 3: Multilingual Translation & Text-to-Speech -->
      <div id="tab-content-translate" class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 hidden flex-col gap-5 hc-card">
        
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <!-- Target Language Picker -->
          <div>
            <label for="lang-select" class="block text-xs font-semibold text-slate-600 mb-1 hc-text">Target Translation Language:</label>
            <select id="lang-select" onchange="translateContent(this.value)" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm font-medium focus:ring-2 focus:ring-indigo-500 hc-input">
              <option value="es">Spanish (Español)</option>
              <option value="hi">Hindi (हिन्दी)</option>
              <option value="fr">French (Français)</option>
              <option value="zh">Mandarin (中文)</option>
              <option value="de">German (Deutsch)</option>
            </select>
          </div>

          <!-- TTS Speed Controls -->
          <div>
            <label for="tts-speed" class="block text-xs font-semibold text-slate-600 mb-1 hc-text">Speech Playback Speed:</label>
            <select id="tts-speed" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm font-medium focus:ring-2 focus:ring-indigo-500 hc-input">
              <option value="0.75">0.75x (Slower Reading)</option>
              <option value="1.0" selected>1.0x (Normal Pace)</option>
              <option value="1.25">1.25x (Faster)</option>
              <option value="1.5">1.5x (Fast)</option>
            </select>
          </div>
        </div>

        <!-- Translated Output Box -->
        <div class="space-y-3">
          <div class="flex justify-between items-center">
            <h3 class="text-sm font-semibold text-slate-700 hc-text">Translated Lecture Segment</h3>
            <button onclick="speakTranslation()" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold flex items-center gap-1.5 transition hc-btn">
              <i class="fa-solid fa-volume-high"></i> Listen Audio (TTS)
            </button>
          </div>

          <div id="translated-box" class="bg-slate-50 p-4 rounded-xl border border-slate-200 text-slate-800 text-sm leading-relaxed min-h-[140px] hc-card">
            <!-- Translated Text Appears Here -->
          </div>
        </div>

        <!-- Accessible Phonetic / Pronunciation Aid -->
        <div class="bg-amber-50 p-3.5 rounded-xl border border-amber-200 text-amber-900 text-xs flex items-start gap-2.5">
          <i class="fa-solid fa-circle-info text-amber-600 text-sm mt-0.5"></i>
          <div>
            <span class="font-bold">Multilingual Learning Support:</span>
            Audio synthesis helps non-native English speakers and auditory learners grasp tricky terminology phonetically.
          </div>
        </div>

      </div>

    </section>

  </main>

  <!-- Footer -->
  <footer class="bg-white border-t border-slate-200 mt-auto py-4 text-center text-xs text-slate-500 hc-card">
    <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-2">
      <p class="hc-text">AccessLearn AI Prototype — Designed for Universal Design for Learning (UDL)</p>
      <div class="flex items-center space-x-4">
        <span class="text-emerald-600 font-medium flex items-center gap-1"><i class="fa-solid fa-check-circle"></i> Speech Recognition Ready</span>
        <span class="text-indigo-600 font-medium flex items-center gap-1"><i class="fa-solid fa-shield-halved"></i> WCAG 2.1 Compliant Design</span>
      </div>
    </div>
  </footer>

  <!-- Application Logic JS -->
  <script>
    // --- Data Store & State Management ---
    const lectureData = [
      {
        id: 1,
        time: "00:15",
        original: "Welcome class. Today we are exploring photosynthesis, the foundational biological process where plants convert light energy into chemical energy.",
        tag: "photosynthesis",
        levels: {
          1: "Today we are learning how plants use light from the sun to make their own food! This process is called photosynthesis.",
          2: "Photosynthesis is the process plants use to change light energy from the sun into chemical energy (food).",
          3: "Photosynthesis is the metabolic pathway in which autotrophs convert solar radiation into stored chemical energy inside sugar molecules.",
          4: "Photosynthesis represents the bioenergetic transduction mechanism whereby photoautotrophs convert photonic energy into biochemical energy stored within carbohydrate bonds."
        },
        translations: {
          es: "Bienvenido a clase. Hoy exploramos la fotosíntesis, el proceso biológico fundamental donde las plantas convierten la energía de la luz en energía química.",
          hi: "कक्षा में आपका स्वागत है। आज हम प्रकाश संश्लेषण (Photosynthesis) का अध्ययन कर रहे हैं, जिसके द्वारा पौधे प्रकाश ऊर्जा को रासायनिक ऊर्जा में बदलते हैं।",
          fr: "Bienvenue en classe. Aujourd'hui, nous explorons la photosynthèse, le processus biologique fondamental par lequel les plantes convertissent l'énergie lumineuse en énergie chimique.",
          zh: "欢迎来到课堂。今天我们将探讨光合作用，这是植物将光能转化为化学能的基础生物过程。",
          de: "Willkommen im Unterricht. Heute erforschen wir die Photosynthese, den grundlegenden biologischen Prozess, bei dem Pflanzen Lichtenergie in chemische Energie umwandeln."
        }
      },
      {
        id: 2,
        time: "01:05",
        original: "Inside plant leaf cells, small structures called chloroplasts contain green pigments known as chlorophyll, which capture sunlight rays directly.",
        tag: "chloroplast",
        levels: {
          1: "Plant leaves have tiny green factory parts called chloroplasts. They have a green color pigment called chlorophyll that catches sunlight.",
          2: "Inside leaf cells, chloroplasts contain green chlorophyll pigments that absorb sunlight.",
          3: "Chloroplasts are specialized organelles housing chlorophyll molecules responsible for absorbing specific wavelengths of light.",
          4: "Intracellular chloroplast organelles synthesize light-harvesting complexes containing chlorophyll pigments tuned for photon absorption."
        },
        translations: {
          es: "Dentro de las células de las hojas, pequeñas estructuras llamadas cloroplastos contienen pigmentos verdes conocidos como clorofila, que capturan los rayos del sol.",
          hi: "पत्तियों की कोशिकाओं के अंदर क्लोरोप्लास्ट नामक संरचनाएं होती हैं जिनमें क्लोरोफिल होता है, जो सूर्य के प्रकाश को अवशोषित करता है।",
          fr: "À l'intérieur des cellules végétales, de petites structures appelées chloroplastes contiennent des pigments verts appelés chlorophylle, qui capturent la lumière du soleil.",
          zh: "在植物叶片细胞内部，称为叶绿体的微小结构包含称为叶绿素的绿色色素，直接捕捉阳光。",
          de: "In den Pflanzenzellen enthalten kleine Strukturen namens Chloroplasten grüne Pigmente (Chlorophyll), die Sonnenlicht absorbieren."
        }
      },
      {
        id: 3,
        time: "02:20",
        original: "Water absorbed by roots and carbon dioxide from the air react together to produce glucose sugar and release oxygen gas as a essential byproduct.",
        tag: "atp",
        levels: {
          1: "Plants drink water from roots and breathe in carbon dioxide gas. They make sugar to eat and release fresh oxygen for us to breathe!",
          2: "Roots take in water and leaves take in carbon dioxide. The plant creates sugar for food and releases oxygen into the air.",
          3: "Water (H2O) and Carbon Dioxide (CO2) undergo chemical reactions powered by light to yield glucose (C6H12O6) and oxygen gas (O2).",
          4: "Oxidative substrate conversion of cellular H2O and atmospheric CO2 synthesizes hexose monosaccharides while releasing molecular O2."
        },
        translations: {
          es: "El agua absorbida por las raíces y el dióxido de carbono del aire reaccionan para producir azúcar glucosa y liberar oxígeno como subproducto.",
          hi: "जड़ों द्वारा सोखा गया पानी और हवा से कार्बन डाइऑक्साइड मिलकर ग्लूकोज (शर्करा) बनाते हैं और ऑक्सीजन बाहर छोड़ते हैं।",
          fr: "L'eau absorbée par les racines et le dioxyde de carbone de l'air réagissent pour produire du glucose et libérer de l'oxygène.",
          zh: "根部吸收的水和空气中的二氧化碳发生反应，生成葡萄糖并释放氧气。",
          de: "Von den Wurzeln aufgenommenes Wasser und Kohlendioxid aus der Luft reagieren zu Glukose und setzen Sauerstoff als Nebenprodukt frei."
        }
      },
      {
        id: 4,
        time: "03:45",
        original: "Finally, the Calvin Cycle takes place within the stroma, utilizing ATP cellular energy to build long-term stored carbohydrates for growth.",
        tag: "calvin",
        levels: {
          1: "Finally, the plant uses stored energy batteries called ATP to build sugar bricks so the plant can grow big and strong.",
          2: "The Calvin Cycle uses stored energy (ATP) inside the plant to build carbohydrates for plant growth.",
          3: "The light-independent reactions (Calvin Cycle) utilize chemical energy carriers ATP and NADPH to fix carbon into organic sugars.",
          4: "Light-independent enzymatic fixation via the Calvin-Benson cycle utilizes synthesized ATP and NADPH reducing potential for carbon assimilation."
        },
        translations: {
          es: "Finalmente, el Ciclo de Calvin utiliza la energía celular ATP para construir carbohidratos almacenados para el crecimiento de la planta.",
          hi: "अंत में, केल्विन चक्र (Calvin Cycle) ATP ऊर्जा का उपयोग करके पौधों की वृद्धि के लिए कार्बोहाइड्रेट का निर्माण करता है।",
          fr: "Enfin, le cycle de Calvin utilise l'énergie cellulaire ATP pour fabriquer des glucides essentiels à la croissance de la plante.",
          zh: "最后，卡尔文循环利用细胞能量ATP合成高能碳水化合物，促进植物生长。",
          de: "Schließlich nutzt der Calvin-Zyklus die Zellenergie ATP, um Kohlenhydrate für das Pflanzenwachstum aufzubauen."
        }
      }
    ];

    const vocabularyGlossary = {
      "photosynthesis": "The natural process where plants use sunlight to make food.",
      "chloroplasts": "Tiny green compartments inside plant cells.",
      "chlorophyll": "The green chemical pigment that catches light.",
      "glucose": "A type of simple sugar that gives living things energy.",
      "ATP": "Adenosine Triphosphate: The main energy coin/currency of living cells.",
      "Calvin Cycle": "The set of chemical steps that turns carbon into sugar."
    };

    let currentReadingLevel = 1;
    let isDemoRunning = false;
    let demoInterval = null;
    let demoIndex = 0;
    let isMicActive = false;
    let recognition = null;
    let currentFilterTag = 'all';

    // --- Core Initialization ---
    window.addEventListener('DOMContentLoaded', () => {
      renderSummary();
      renderTranscriptList(lectureData);
      translateContent('es');
      initWebSpeech();
    });

    // --- Web Speech API (Microphone Speech Recognition) ---
    function initWebSpeech() {
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onresult = (event) => {
          let interimTranscript = '';
          let finalTranscript = '';

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript;
            } else {
              interimTranscript += event.results[i][0].transcript;
            }
          }

          if (finalTranscript) {
            appendLiveCaption(finalTranscript, true);
          } else if (interimTranscript) {
            appendLiveCaption(interimTranscript, false);
          }
        };

        recognition.onerror = (err) => {
          console.warn("Speech Recognition Error: ", err);
          updateStatus("Mic Error", "rose");
        };

        recognition.onend = () => {
          if (isMicActive) recognition.start();
        };
      }
    }

    function toggleMic() {
      if (!recognition) {
        alert("Web Speech API is not supported in this browser version. Please try Google Chrome or Edge, or use the 'Simulate Demo' mode!");
        return;
      }

      if (isDemoRunning) stopDemoSimulation();

      const micBtn = document.getElementById('btn-mic-toggle');
      const micIcon = document.getElementById('mic-icon');
      const micText = document.getElementById('mic-text');

      if (!isMicActive) {
        try {
          recognition.start();
          isMicActive = true;
          micBtn.classList.replace('bg-indigo-600', 'bg-rose-600');
          micBtn.classList.replace('hover:bg-indigo-700', 'hover:bg-rose-700');
          micIcon.className = "fa-solid fa-microphone-slash";
          micText.innerText = "Stop Mic";
          setVisualizerState(true);
          updateStatus("Live Listening", "emerald");
        } catch (e) {
          console.error(e);
        }
      } else {
        isMicActive = false;
        recognition.stop();
        micBtn.classList.replace('bg-rose-600', 'bg-indigo-600');
        micBtn.classList.replace('hover:bg-rose-700', 'hover:bg-indigo-700');
        micIcon.className = "fa-solid fa-microphone";
        micText.innerText = "Start Mic";
        setVisualizerState(false);
        updateStatus("Standby", "slate");
      }
    }

    // --- Simulated Demo Lecture Player ---
    function toggleDemoSimulation() {
      if (isMicActive) toggleMic();

      if (isDemoRunning) {
        stopDemoSimulation();
      } else {
        startDemoSimulation();
      }
    }

    function startDemoSimulation() {
      isDemoRunning = true;
      demoIndex = 0;
      const demoBtn = document.getElementById('btn-demo-toggle');
      document.getElementById('demo-icon').className = "fa-solid fa-pause text-amber-600";
      document.getElementById('demo-text').innerText = "Pause Demo";
      setVisualizerState(true);
      updateStatus("Demo Playing", "amber");

      // Deliver first line immediately
      playNextDemoSegment();

      demoInterval = setInterval(() => {
        playNextDemoSegment();
      }, 4500);
    }

    function stopDemoSimulation() {
      isDemoRunning = false;
      clearInterval(demoInterval);
      document.getElementById('demo-icon').className = "fa-solid fa-play";
      document.getElementById('demo-text').innerText = "Simulate Demo";
      setVisualizerState(false);
      updateStatus("Standby", "slate");
    }

    function playNextDemoSegment() {
      if (demoIndex >= lectureData.length) {
        demoIndex = 0; // Loop back
      }
      const segment = lectureData[demoIndex];
      appendLiveCaption(`[${segment.time}] ${segment.original}`, true);
      demoIndex++;
    }

    function appendLiveCaption(text, isFinal) {
      const placeholder = document.getElementById('caption-placeholder');
      if (placeholder) placeholder.remove();

      const stream = document.getElementById('caption-stream');
      
      // Update or create active line
      let activeLine = document.getElementById('active-interim-line');
      if (!activeLine) {
        activeLine = document.createElement('div');
        activeLine.id = 'active-interim-line';
        activeLine.className = 'p-2 rounded bg-indigo-950/80 border-l-4 border-indigo-400 text-indigo-100 transition-all';
        stream.appendChild(activeLine);
      }

      activeLine.innerHTML = formatGlossaryTooltips(text);
      if (isFinal) {
        activeLine.removeAttribute('id');
        activeLine.className = 'p-2 rounded bg-slate-800/80 border-l-4 border-emerald-500 text-slate-100 transition-all';
      }

      // Auto scroll to bottom
      const win = document.getElementById('caption-window');
      win.scrollTop = win.scrollHeight;
    }

    function clearCaptions() {
      document.getElementById('caption-stream').innerHTML = '';
    }

    // --- Adaptive Summarization & Reading Levels ---
    function updateReadingLevel(val) {
      currentReadingLevel = parseInt(val);
      const labels = {
        1: "Elementary (Grades 1-5)",
        2: "Middle School (Grades 6-8)",
        3: "High School (Grades 9-12)",
        4: "Academic / University Level"
      };
      document.getElementById('level-indicator').innerText = labels[currentReadingLevel];
      renderSummary();
    }

    function renderSummary() {
      const container = document.getElementById('summary-display');
      const bulletsContainer = document.getElementById('summary-bullets');

      let combinedParagraph = lectureData
        .map(item => item.levels[currentReadingLevel])
        .join(" ");

      container.innerHTML = `<p>${formatGlossaryTooltips(combinedParagraph)}</p>`;

      // Render Takeaway bullets based on level
      const bulletList = [
        `<strong>Light Power:</strong> Plants trap sunshine using green ${formatGlossaryTooltips('chlorophyll')}.`,
        `<strong>Ingredients:</strong> Water + Carbon Dioxide combine inside cells.`,
        `<strong>Products:</strong> Generates ${formatGlossaryTooltips('glucose')} (sugar food) and oxygen gas.`
      ];

      bulletsContainer.innerHTML = bulletList
        .map(b => `<li class="flex items-start gap-2"><i class="fa-solid fa-circle-check text-emerald-600 mt-1"></i><span>${b}</span></li>`)
        .join('');
    }

    // Interactive Hover Tooltips for Vocabulary
    function formatGlossaryTooltips(text) {
      let formatted = text;
      Object.keys(vocabularyGlossary).forEach(term => {
        const regex = new RegExp(`\\b(${term})\\b`, 'gi');
        formatted = formatted.replace(regex, `<span class="tooltip-term text-indigo-600 font-semibold" title="${vocabularyGlossary[term]}">$1</span>`);
      });
      return formatted;
    }

    // --- Searchable Transcript & Filtering ---
    function renderTranscriptList(items) {
      const listContainer = document.getElementById('full-transcript-list');
      const countLabel = document.getElementById('search-result-count');

      countLabel.innerText = `Showing ${items.length} of ${lectureData.length} timestamps`;

      if (items.length === 0) {
        listContainer.innerHTML = `<div class="p-8 text-center text-slate-400 text-sm">No matching timestamp notes found. Try adjusting your search keyword.</div>`;
        return;
      }

      listContainer.innerHTML = items.map(item => `
        <div class="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:shadow-sm transition flex gap-3 items-start hc-card">
          <span class="font-mono text-xs font-bold px-2 py-1 bg-indigo-100 text-indigo-700 rounded-md hc-badge">${item.time}</span>
          <div class="flex-grow">
            <p class="text-sm text-slate-800 leading-snug hc-text">${formatGlossaryTooltips(item.original)}</p>
            <div class="mt-1.5 flex items-center gap-2">
              <span class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">#${item.tag}</span>
            </div>
          </div>
          <button onclick="speakText('${escapeQuotes(item.original)}')" class="text-slate-400 hover:text-indigo-600 p-1 transition" title="Read Aloud">
            <i class="fa-solid fa-volume-low text-xs"></i>
          </button>
        </div>
      `).join('');
    }

    function handleSearch(query) {
      const q = query.toLowerCase().trim();
      let filtered = lectureData.filter(item => 
        item.original.toLowerCase().includes(q) || item.tag.toLowerCase().includes(q)
      );

      if (currentFilterTag !== 'all') {
        filtered = filtered.filter(item => item.tag === currentFilterTag);
      }

      renderTranscriptList(filtered);
    }

    function filterByTag(tag) {
      currentFilterTag = tag;
      const buttons = document.querySelectorAll('#topic-tags button');
      buttons.forEach(btn => {
        btn.className = "px-3 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition hc-badge";
      });
      event.target.className = "px-3 py-1 rounded-lg text-xs font-medium bg-indigo-600 text-white transition hc-btn";

      handleSearch(document.getElementById('transcript-search').value);
    }

    // --- Multilingual Translation & TTS ---
    function translateContent(langCode) {
      const translatedBox = document.getElementById('translated-box');
      const translatedText = lectureData
        .map(item => `[${item.time}] ${item.translations[langCode] || item.original}`)
        .join('<br><br>');

      translatedBox.innerHTML = translatedText;
    }

    function speakTranslation() {
      const lang = document.getElementById('lang-select').value;
      const container = document.getElementById('translated-box');
      const text = container.innerText;
      speakText(text, lang);
    }

    function speakText(text, lang = 'en-US') {
      if (!('speechSynthesis' in window)) {
        alert("Text-to-Speech is not supported in this browser.");
        return;
      }

      window.speechSynthesis.cancel(); // Stop ongoing speech

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang;
      
      const speedSelect = document.getElementById('tts-speed');
      if (speedSelect) {
        utterance.rate = parseFloat(speedSelect.value);
      }

      window.speechSynthesis.speak(utterance);
    }

    // --- Accessibility Utilities (Font Size & High Contrast) ---
    function setFontSize(size) {
      const stream = document.getElementById('caption-stream');
      const btnSm = document.getElementById('btn-font-sm');
      const btnMd = document.getElementById('btn-font-md');
      const btnLg = document.getElementById('btn-font-lg');

      btnSm.classList.replace('bg-indigo-500', 'bg-indigo-700');
      btnMd.classList.replace('bg-indigo-500', 'bg-indigo-700');
      btnLg.classList.replace('bg-indigo-500', 'bg-indigo-700');

      if (size === 'sm') {
        stream.style.fontSize = '14px';
        btnSm.classList.replace('bg-indigo-700', 'bg-indigo-500');
      } else if (size === 'md') {
        stream.style.fontSize = '18px';
        btnMd.classList.replace('bg-indigo-700', 'bg-indigo-500');
      } else if (size === 'lg') {
        stream.style.fontSize = '24px';
        btnLg.classList.replace('bg-indigo-700', 'bg-indigo-500');
      }
    }

    function toggleHighContrast() {
      document.body.classList.toggle('high-contrast');
      const isHc = document.body.classList.contains('high-contrast');
      document.getElementById('contrast-label').innerText = isHc ? "Standard Contrast" : "High Contrast";
    }

    // Tab Switcher
    function switchTab(tabKey) {
      ['summary', 'notes', 'translate'].forEach(key => {
        const btn = document.getElementById(`tab-btn-${key}`);
        const content = document.getElementById(`tab-content-${key}`);
        
        if (key === tabKey) {
          btn.className = "flex-1 py-2 px-3 rounded-xl text-xs sm:text-sm font-semibold transition bg-indigo-600 text-white hc-btn";
          content.classList.remove('hidden');
          content.classList.add('flex');
        } else {
          btn.className = "flex-1 py-2 px-3 rounded-xl text-xs sm:text-sm font-semibold transition text-slate-600 hover:bg-slate-100 hc-btn";
          content.classList.add('hidden');
          content.classList.remove('flex');
        }
      });
    }

    // Helper UI Updaters
    function setVisualizerState(active) {
      const viz = document.getElementById('audio-visualizer');
      if (active) {
        viz.classList.remove('opacity-50');
        viz.innerHTML = `
          <span class="w-1 bg-emerald-400 rounded-full animate-bar-1"></span>
          <span class="w-1 bg-emerald-400 rounded-full animate-bar-2"></span>
          <span class="w-1 bg-emerald-400 rounded-full animate-bar-3"></span>
          <span class="w-1 bg-emerald-400 rounded-full animate-bar-4"></span>
          <span class="w-1 bg-emerald-400 rounded-full animate-bar-5"></span>
          <span class="text-xs text-emerald-400 font-mono ml-2 font-semibold">Audio Active</span>
        `;
      } else {
        viz.classList.add('opacity-50');
        viz.innerHTML = `
          <span class="w-1 bg-slate-500 rounded-full h-1.5"></span>
          <span class="w-1 bg-slate-500 rounded-full h-1.5"></span>
          <span class="w-1 bg-slate-500 rounded-full h-1.5"></span>
          <span class="text-xs text-slate-400 font-mono ml-2">Audio Inactive</span>
        `;
      }
    }

    function updateStatus(text, color) {
      const badge = document.getElementById('status-badge');
      const colors = {
        emerald: 'bg-emerald-100 text-emerald-800',
        amber: 'bg-amber-100 text-amber-800',
        rose: 'bg-rose-100 text-rose-800',
        slate: 'bg-slate-100 text-slate-600'
      };
      badge.className = `px-2.5 py-1 text-xs rounded-full font-medium hc-badge ${colors[color]}`;
      badge.innerHTML = `<i class="fa-solid fa-circle text-[8px] mr-1"></i> ${text}`;
    }

    function exportTranscript(format) {
      let textContent = "# AccessLearn AI - Lecture Notes & Transcript\n\n";
      lectureData.forEach(item => {
        textContent += `[${item.time}] ${item.original}\n\n`;
      });

      const blob = new Blob([textContent], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `lecture-notes-${new Date().toISOString().slice(0,10)}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    }

    function escapeQuotes(str) {
      return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
    }
  </script>
</body>
</html>
