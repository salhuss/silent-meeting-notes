# Silent Meeting Notes

**AI-powered multi-speaker meeting transcription and summarization tool**  
Turns raw audio into structured notes with:

- **Summary**: Key points in bullet form  
- **Decisions**: Explicit choices made in the meeting  
- **Action Items**: Owner, task, and due date (optionally exportable to `.ics` calendar)  
- **Speaker Transcript**: Timestamped transcript with S1/S2 speaker tags

---

## ✨ Features

- 🎙️ **Speech-to-text** with [faster-whisper](https://github.com/guillaumekln/faster-whisper) (local Whisper model)
- 🧑‍🤝‍🧑 **Speaker diarization** with [resemblyzer](https://github.com/resemble-ai/Resemblyzer) + KMeans
- 🧠 **LLM-powered structuring** into Summary, Decisions, and Action Items
- 📄 Export formats:
  - `transcript.txt` / `.json` / `.srt`
  - `speaker_transcript.md` (speaker-tagged Markdown)
  - `notes.md` / `.json`
  - Optional `action_items.ics` for calendar import
- ⚡ Works locally; LLM summarization optional (requires `OPENAI_API_KEY`)

---

## 📦 Installation

Clone this repo and set up a Python environment:

```bash
git clone https://github.com/<your-username>/silent-meeting-notes.git
cd silent-meeting-notes

python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

pip install -r requirements.txt

export WHISPER_MODEL=tiny  # or base/small/medium/large-v3
python -m meeting_notes.cli path/to/audio.wav --out out/

python -m meeting_notes.cli path/to/audio.wav \
    --out out/ \
    --speakers 2-4 \
    --calendar \
    --tz "America/New_York" \
    --due_hour 17

out/
├── transcript.txt             # Plain text transcript
├── transcript.json            # Transcript with segments + word timings
├── transcript.srt              # SubRip subtitles
├── speaker_turns.json         # JSON list of speaker-attributed turns
├── speaker_transcript.md      # Markdown with S1/S2 labels + timestamps
├── notes.json                 # Structured notes (summary/decisions/actions)
├── notes.md                   # Pretty Markdown notes
└── action_items.ics           # (Optional) Calendar events for action items


# Meeting Notes

## Summary
- Discussed Q3 hiring goals
- Updated on product release delays
- Marketing campaign performance reviewed

## Decisions
- Launch date moved to September 15th

## Action Items
- **S2** — Prepare revised launch plan _(due 2025-08-22)_
- **S1** — Share updated campaign metrics _(due 2025-08-22)_
