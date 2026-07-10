# Setup Documentation — Phase 1 & Phase 2

## Prerequisites (both phases)
- Python 3.10 or higher
- pip
- An OpenAI API key (used for the conversation LLM in both phases)
  - Sign up at https://platform.openai.com and create a key
  - *(Alternative: Ollama, free and fully local — see "Optional: using Ollama instead" below)*
- A microphone and browser (Chrome recommended) — Phase 2 only

## 1. Get the project files
Unzip the project folder. You should see:
```
sales_agent/
├── data/
│   ├── leads_crm.xlsx
│   └── knowledge_base.md
├── build_crm.py
├── prompts.py
├── llm_client.py
├── excel_manager.py
├── call_simulator.py
├── summarizer.py
├── main.py                  # Phase 1 entry point
├── server.py                 # Phase 2 entry point
├── stt_client.py              # Phase 2 — Faster-Whisper
├── tts_client.py               # Phase 2 — Edge-TTS
├── static/index.html
├── requirements.txt
├── .env.example
└── .gitignore
```

## 2. Install dependencies
From inside the `sales_agent/` folder:
```bash
pip install -r requirements.txt
```

If you're setting up Phase 2's voice stack manually rather than via
`requirements.txt`, the two key packages are:
```bash
pip install faster-whisper edge-tts
```
- `faster-whisper` will download a Whisper model (e.g. `base`) automatically
  the first time it runs — this can take a minute depending on your
  connection, and only happens once.
- `edge-tts` needs no model download and no API key — it calls Microsoft's
  free online TTS voices directly.

## 3. Configure environment variables
Copy the example env file and fill it in:
```bash
cp .env.example .env
```
Open `.env` and set at minimum:
```
LLM_PROVIDER=groq
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=llama-3.3-70b-versatile

TTS_PROVIDER=edge
EDGE_TTS_VOICE=en-IN-NeerjaNeural
```
Phase 2's STT/TTS providers (Faster-Whisper, Edge-TTS) don't need API keys,
so no further config is required there — just make sure `stt_client.py` /
`tts_client.py` are pointed at those providers (they are, by default, in
this build).

### Optional: using Ollama instead of OpenAI (free, fully local LLM)
1. Install from https://ollama.com
2. `ollama pull llama3`
3. Make sure `ollama serve` is running (usually starts automatically)
4. In `.env`, set `LLM_PROVIDER=ollama`

## 4. Set up the CRM data
A sample `data/leads_crm.xlsx` is already included with 5 leads (a mix of
`Pending`, `Completed`, and `Opted-out`), plus `data/knowledge_base.md`
with sample company info.
- To reset the CRM back to the original sample data at any point:
  ```bash
  python build_crm.py
  ```
- To use your own leads, edit `leads_crm.xlsx` directly, keeping the same
  column headers. To use your own company info, edit `knowledge_base.md`.

## 5. Run Phase 1 (text-based call, terminal)
```bash
python main.py
```
- Pulls the next `Pending` lead from the CRM.
- You play the lead by typing replies in the terminal.
- Type `hangup` to end the call.
- On end, the transcript is summarized and written back into
  `data/leads_crm.xlsx` automatically.
- Run it again to move to the next pending lead.

**Quick verification it worked:** open `data/leads_crm.xlsx` afterward and
confirm the row you just called has `Call Status`, `Lead Qualification`,
`Conversation Summary`, and `Last Contacted Timestamp` filled in, and
`Lead Status` changed to `Completed`.

## 6. Run Phase 2 (voice call, browser)
```bash
uvicorn server:app --reload
```
Then open **http://localhost:8000** in your browser and allow microphone
access when prompted.
- Click **Start Call** — the agent speaks its opening line out loud.
- **Hold** the talk button while speaking, **release** to send — Faster-Whisper
  transcribes it, the same conversation engine replies, Edge-TTS speaks it
  back.
- Click **End Call** to finish — the CRM is updated exactly as in Phase 1.

## Troubleshooting
| Symptom | Likely cause / fix |
|---|---|
| `No pending leads found` | All leads are `Completed`/`Opted-out` — run `python build_crm.py` to reset the sample data. |
| `OPENAI_API_KEY` errors | Check `.env` is filled in and actually loaded (some setups need `from dotenv import load_dotenv; load_dotenv()` added at the top of `main.py`/`server.py`, or export the vars manually before running). |
| Faster-Whisper is slow on first run | Normal — it's downloading the model. Subsequent runs are fast. |
| No microphone prompt in browser | Use Chrome, and make sure the page is loaded over `http://localhost` (not a raw file path) — browsers block mic access otherwise. |
| Edge-TTS returns no audio / connection error | Requires an internet connection (it's an online service, not local) — check connectivity. |
| Excel file won't update / "file in use" error | Close the `.xlsx` file in Excel/Google Sheets before running a call — some spreadsheet apps lock the file while open. |

## What each phase proves
- **Phase 1** validates the core assignment logic: lead management,
  qualification, knowledge-base-grounded answers, objection handling,
  meeting booking, and structured CRM updates — independent of voice.
- **Phase 2** validates the same logic works end-to-end with real audio
  input/output, using a fully free local+cloud voice stack (Faster-Whisper
  + Edge-TTS)




# AI Voice Sales Agent — Phase 1
<img width="2720" height="1816" alt="phase1_data_workflow" src="https://github.com/user-attachments/assets/c554af92-48ab-450d-8dc3-bd64d34297c2" />

## What this phase covers
Phase 1 builds the "brain" of the AI sales agent and its connection to the
Excel CRM — everything except real voice/telephony, which comes in later
phases. It proves the hardest conceptual part of the assignment: an AI that
can hold a real qualifying sales conversation and turn it into clean,
structured CRM data automatically.

## What was built
1. **Lead management (Excel as CRM)**
   - Reads leads from `data/leads_crm.xlsx`.
   - Automatically finds the next lead marked `Pending`.
   - Skips leads marked `Completed` or `Opted-out` — they're never contacted.

2. **Conversation engine (text-based simulated call)**
   - An LLM-driven agent persona ("Aisha") that introduces the company,
     asks qualification questions one at a time, answers product/pricing
     questions strictly from a knowledge base file, handles common
     objections, and closes the call professionally.
   - Simulated as a text chat for this phase (you type as the lead) so the
     conversation logic could be designed and tested quickly, before adding
     the complexity of real voice.

3. **Knowledge base grounding**
   - Company/product info lives in `data/knowledge_base.md`.
   - The agent is instructed to answer only from this file, and to say
     it'll follow up rather than invent an answer if something isn't
     covered — avoids hallucinated pricing/policy claims.

4. **Post-call summarization**
   - A second LLM call reads the full transcript and extracts structured
     JSON: call status, lead qualification, a plain-language summary,
     customer requirements, objections raised, follow-up date, and meeting
     date/time.

5. **Excel CRM update**
   - Every field above is written back into the correct row.
   - Lead Status automatically flips to `Completed` once a call reaches an
     outcome (meeting booked / not interested), or stays `Pending` if the
     call didn't connect.
   - Last Contacted Timestamp is stamped automatically.

## Tech used
Python, GROQ API (or Ollama for a fully local/free alternative),
openpyxl/pandas for Excel I/O. No telephony or audio yet — that's Phase 2/3.

## How to run it
See the setup steps in the main project README — in short: `pip install -r
requirements.txt`, add an API key to `.env`, then `python main.py`. It pulls
the next pending lead and starts a simulated call in the terminal.


# AI Voice Sales Agent — Phase 2 

<img width="2720" height="2240" alt="phase2_data_workflow" src="https://github.com/user-attachments/assets/a4935703-71c1-435f-a6ba-9e49032e4283" />


## What this phase covers
Phase 2 adds real voice to the Phase 1 conversation engine — you speak into
your browser's microphone, and the AI sales agent replies out loud. The
underlying conversation brain, knowledge base, and Excel CRM logic from
Phase 1 are reused unchanged; only the input/output layer changed from
typed text to real audio.

## What was built
1. **Browser call interface**
   - A simple web page with a "Start Call" button and a push-to-talk mic
     button — hold to speak, release to send.
   - Plays the agent's spoken reply automatically after each turn.
   - Shows a live text transcript alongside the audio, and a results panel
     once the call ends showing exactly what got written to the CRM.

2. **Speech-to-Text — Faster-Whisper**
   - Converts the recorded mic audio into text.
   - Runs fully locally on the machine, no API key or internet call needed
     for transcription itself — a CTranslate2-optimized reimplementation of
     OpenAI's Whisper model, chosen for being noticeably faster and lighter
     than the original `openai-whisper` package while keeping the same
     accuracy.

3. **Text-to-Speech — Edge-TTS (Microsoft)**
   - Converts the agent's text reply into natural-sounding speech.
   - Free, no API key required — uses Microsoft Edge's online neural TTS
     voices, called asynchronously from the backend.

4. **Same conversation brain as Phase 1**
   - The transcribed text is passed straight into the same LLM-driven
     conversation logic (qualification questions, knowledge-base-grounded
     answers, objection handling, closing) — nothing about the sales logic
     itself changed.

5. **Same CRM update flow as Phase 1**
   - When the call ends, the full transcript is summarized into structured
     fields and written back into `data/leads_crm.xlsx`, exactly as in
     Phase 1.

## Tech used
Python, FastAPI (backend server), vanilla JS + MediaRecorder API (browser
mic capture), **Faster-Whisper** (speech-to-text, local), **Edge-TTS**
(text-to-speech, Microsoft's free online voices), Groq API/Ollama for the
conversation LLM (unchanged from Phase 1).

## Why this combination
- Keeps the whole voice layer free — no paid STT/TTS API key needed, only
  the LLM key from Phase 1 is required.
- Faster-Whisper's local inference means no audio data leaves the machine
  during transcription, which also keeps latency low and predictable.
- Edge-TTS gives natural-sounding voices without needing an ElevenLabs
  subscription or setting up Piper's local voice models manually.

## Design choice: push-to-talk, not always-listening
The interface uses a hold-to-talk button rather than continuous listening.
This avoids the agent picking up its own voice through the speakers and
sidesteps the need for real-time interruption/turn-taking logic, which is
a genuinely hard problem — that's addressed properly in Phase 3 using a
streaming voice framework built for it.

## How to run it
See the setup steps in the main project README for installing dependencies
and starting the server, then open the local web page, click **Start
Call**, and hold the talk button while speaking.
