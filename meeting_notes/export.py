# meeting_notes/export.py
from pathlib import Path
import json

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def srt_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def segments_to_srt(segments):
    lines = []
    for i, seg in enumerate(segments, start=1):
        start = srt_timestamp(seg["start"])
        end = srt_timestamp(seg["end"])
        text = seg["text"]
        lines.append(str(i))
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")  # blank line
    return "\n".join(lines).strip() + "\n"

# meeting_notes/export.py  (append these helpers)
def write_speaker_md(path: Path, turns):
    lines = ["# Speaker Transcript\n"]
    for t in turns:
        lines.append(f"**{t['speaker']}** [{srt_timestamp(t['start'])}–{srt_timestamp(t['end'])}]: {t['text']}")
    lines.append("")  # trailing newline
    write_text(path, "\n".join(lines))

