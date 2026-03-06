# Clara Answers — AI Voice Agent Configuration Pipeline

An end-to-end automation pipeline that converts call transcripts into deployable Retell AI voice agent configurations. Built as a zero-cost, reproducible system for onboarding service trade businesses onto Clara Answers.

---

## What This Does

```
Demo Call Transcript      →  Pipeline A  →  Account Memo v1  +  Agent Spec v1
Onboarding Transcript     →  Pipeline B  →  Account Memo v2  +  Agent Spec v2  +  Changelog
```

- **Pipeline A** ingests a demo call transcript, extracts structured business configuration using an LLM, and generates a preliminary Retell agent spec (v1).
- **Pipeline B** ingests an onboarding call transcript, computes a diff against v1, applies the patch, and produces an updated agent spec (v2) with a full changelog.
- Both pipelines are repeatable, idempotent, and batch-capable.

---

## How It Works

Imagine you're onboarding a new client — a small electrical company. They hop on a call, explain their business, mention their hours, talk about a VIP customer who calls at 2am sometimes. Normally, someone on your team listens to that recording, manually fills in a config sheet, and eventually sets up the AI agent by hand.

**This pipeline replaces all of that.**

Here's the journey a single call takes through the system:

**1. The call becomes text**
If you have an audio file, `transcribe.py` runs it through OpenAI Whisper locally on your machine — no cloud, no cost, no data leaving your computer. The result is a plain `.txt` transcript dropped into `data/transcripts/`. Already have a transcript? Skip straight to step 2.

**2. The text gets read and understood**
`extract.py` opens that file with a single Python call:
```python
transcript = Path(transcript_path).read_text(encoding="utf-8")
```
That entire conversation — every detail Ben mentioned about his pricing, his VIP client, his business hours — gets stuffed into a carefully engineered prompt and sent to Groq's LLM. The prompt doesn't say *"summarize this"*. It says *"fill in this exact JSON schema, and if something wasn't explicitly said, leave it null — do not guess."*

The result is an **Account Memo**: a clean, structured JSON with business hours, emergency rules, pricing, special clients, and a list of anything that's still genuinely unknown.

**3. The memo becomes an agent**
`generate_prompt.py` takes that memo and asks the LLM a completely different question: *"given everything we know about this business, write a full AI voice agent script."* It comes back with Clara's exact words — what to say when answering, how to handle emergencies, when to mention pricing, what to do if a transfer fails. This is the **Agent Spec v1**.

**4. The onboarding call refines everything**
After the client signs up, there's a second call with more precise details. `patch.py` sends both the existing v1 memo AND the new transcript to the LLM and asks: *"what changed?"* Only the delta comes back — not a full re-extraction. That patch gets deep-merged onto v1 to produce **v2**, and a **changelog** is written explaining every single change and why it happened.

**5. It scales without any extra effort**
Drop 10 transcripts in the folder, run `python run_all.py`, get 10 account memos, 10 agent specs, and 10 changelogs. The pipeline figures out which files are demos and which are onboarding calls purely from the filename.

---

## Architecture

```
clara-pipeline/
├── data/
│   └── transcripts/               # Input transcripts (demo + onboarding)
├── outputs/
│   └── accounts/
│       └── account_001/
│           ├── v1/
│           │   ├── account_memo.json    # Extracted config from demo call
│           │   └── agent_spec.json      # Retell agent draft (v1)
│           └── v2/
│               ├── account_memo.json    # Updated config from onboarding
│               └── agent_spec.json      # Retell agent draft (v2)
├── changelog/
│   ├── account_001_changelog.md         # Human-readable diff v1 -> v2
│   └── account_001_patch.json           # Raw patch data
├── scripts/
│   ├── extract.py                       # LLM extraction -> Account Memo JSON
│   ├── generate_prompt.py               # Account Memo -> Retell Agent Spec
│   ├── patch.py                         # v1 -> v2 diff + changelog
│   └── transcribe.py                    # Whisper audio transcription (optional)
├── workflows/
│   ├── pipeline_a.py                    # Demo call -> v1 orchestrator
│   └── pipeline_b.py                    # Onboarding -> v2 orchestrator
├── run_all.py                           # Batch runner for all accounts
├── requirements.txt
├── .env.example
└── README.md
```

---

## Stack

| Layer | Tool | Why |
|---|---|---|
| LLM | Groq (llama-3.3-70b-versatile) | Free tier, fast, reliable |
| Transcription | OpenAI Whisper (local) | Free, runs offline |
| Storage | Local JSON + GitHub | Simple, versioned, reproducible |
| Orchestration | Python scripts | No infra needed, fully portable |

---

## Setup

### 1. Clone the repo
```bash
git clone <your-repo-url>
cd clara-pipeline
```

### 2. Create and activate virtual environment
```bash
python -m venv venv

# Mac/Linux:
source venv/bin/activate

# Windows (Git Bash):
source venv/Scripts/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Get your free Groq API key
- Go to [console.groq.com](https://console.groq.com)
- Sign up (free, no credit card required)
- Click **API Keys** → **Create API Key**
- Copy the key

### 5. Configure environment
```bash
cp .env.example .env
# Open .env and paste your Groq API key
```

Your `.env` should look like:
```
GROQ_API_KEY=gsk_your_key_here
```

---

## Running the Pipeline

### Transcript naming convention
Place transcript files in `data/transcripts/` using this format:
```
data/transcripts/account_001_demo.txt
data/transcripts/account_001_onboarding.txt
data/transcripts/account_002_demo.txt
data/transcripts/account_002_onboarding.txt
```

### Pipeline A — Demo call → Agent v1
```bash
python workflows/pipeline_a.py --account_id account_001 --transcript data/transcripts/account_001_demo.txt
```

**Output:**
```
outputs/accounts/account_001/v1/account_memo.json
outputs/accounts/account_001/v1/agent_spec.json
```

### Pipeline B — Onboarding → Agent v2 + Changelog
```bash
python workflows/pipeline_b.py --account_id account_001 --transcript data/transcripts/account_001_onboarding.txt
```

**Output:**
```
outputs/accounts/account_001/v2/account_memo.json
outputs/accounts/account_001/v2/agent_spec.json
changelog/account_001_changelog.md
changelog/account_001_patch.json
```

> Pipeline B requires Pipeline A to have run first for the same account_id.

### Batch — Run all accounts at once
```bash
python run_all.py
```

This auto-detects all transcripts in `data/transcripts/`, runs Pipeline A for all demo files first, then Pipeline B for all onboarding files. Running it twice is safe — outputs are overwritten cleanly.

---

## Transcription

If you have audio files instead of transcripts, transcribe them locally using Whisper:

```bash
# Requires ffmpeg to be installed and on PATH
python scripts/transcribe.py --audio path/to/audio.mp3 --account_id account_001 --type demo
```

This saves the transcript to `data/transcripts/account_001_demo.txt` automatically.

If ffmpeg is not available, convert audio to MP3 using [cloudconvert.com](https://cloudconvert.com) first.

---

## Output Format

### Account Memo JSON
Structured configuration extracted from the transcript:
- Business hours, timezone, contact info
- Services supported and pricing
- Emergency definitions and routing rules
- Special client handling (e.g. VIP after-hours clients)
- Call transfer rules and fallback logic
- `questions_or_unknowns` — flags genuinely missing info without hallucinating

### Retell Agent Spec JSON
Production-ready agent configuration including:
- Full system prompt covering business hours and after-hours flows
- Step-by-step flow scripts (greeting, routing, fallback, close)
- Call transfer protocol and fallback protocol
- Pricing disclosure logic
- Tool invocation placeholders (background actions, never mentioned to caller)
- Version tag (v1 or v2)

### Changelog
Human-readable markdown diff showing:
- Every field that changed from v1 to v2
- Old value vs new value
- Reason for the change (grounded in the transcript)
- Resolved unknowns and any new unknowns

---

## Retell Integration

Since Retell's free tier has limited API access, the pipeline outputs a complete `agent_spec.json` ready for manual import:

1. Log into your [Retell dashboard](https://app.retellai.com)
2. Create a new agent
3. Copy `system_prompt` from `agent_spec.json` into the agent's system prompt field
4. Set the voice, transfer number, and timezone from `key_variables`
5. Use `tool_invocation_placeholders` as a reference for configuring tools

With paid Retell API access, `pipeline_a.py` and `pipeline_b.py` can be extended to call the Retell API directly and auto-create/update agents.

---

## Known Limitations

- Whisper transcription requires ffmpeg installed locally on Windows
- Groq free tier has rate limits — for large batches (20+ accounts), add a small delay between requests
- No direct Retell API integration (mocked via JSON spec output)
- Pipeline B uses the same transcript as demo if no separate onboarding call is available
- Timezone is not always extractable from calls — flagged in `questions_or_unknowns`

---

## What I Would Improve with Production Access

- **Direct Retell API integration** — auto-create and update agents via API on each pipeline run
- **Supabase storage** — replace local JSON files with a queryable database
- **Webhook triggers** — trigger pipelines automatically when a new recording lands in storage
- **Asana integration** — auto-create onboarding task per account after Pipeline A runs
- **Confidence scoring** — flag low-confidence extractions for human review
- **Diff viewer UI** — simple web page showing v1 vs v2 side by side with highlights
- **Retry + error logging** — structured logs per account with retry on transient LLM failures