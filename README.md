# Silent Meeting Notes

AI-powered multi-speaker meeting transcription and summarization tool that turns raw audio into structured notes with **summary**, **decisions**, and **action items**.

## MVP Features
- Transcribe local audio files (later: live mic).
- Lightweight speaker diarization (S1, S2, …).
- LLM-powered structuring: summary, decisions, action items (owner + suggested due date).
- Exports to `notes.md` and `notes.json`.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m meeting_notes.cli --help
