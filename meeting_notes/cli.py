# meeting_notes/cli.py
import typer
from pathlib import Path

from .asr import transcribe_file
from .diarize import diarize_file, attach_speakers
from .summarize import structure_notes
from .export import (
    write_text,
    write_json,
    segments_to_srt,
    write_speaker_md,
    write_notes_md,
)

app = typer.Typer(help="Silent Meeting Notes CLI")

@app.command()
def main(
    input: str = typer.Argument(..., help="Path to audio file (wav/mp3/m4a)"),
    out: str = typer.Option("out", help="Output directory"),
    model: str = typer.Option(
        None,
        help="Whisper model size (tiny/base/small/medium/large-v3). "
             "Default: env WHISPER_MODEL or 'base'"
    ),
    srt: bool = typer.Option(True, help="Also write transcript.srt"),
    speakers: str = typer.Option(
        "2-4",
        help="Speaker cluster range, e.g. '2-5' or a fixed '2'"
    ),
):
    """
    v0.3:
    1) Transcribe audio with faster-whisper (txt/json/SRT)
    2) Diarize with resemblyzer + KMeans → speaker-attributed turns
    3) LLM structuring → summary, decisions, action items
    4) Exports: transcript.*, speaker_transcript.md, notes.md/json
    """
    out_p = Path(out)
    out_p.mkdir(parents=True, exist_ok=True)

    # 1) ASR
    typer.echo("🎙️ Transcribing…")
    asr = transcribe_file(input, model_size=model)
    write_text(out_p / "transcript.txt", asr["text"])
    write_json(out_p / "transcript.json", asr)
    if srt:
        write_text(out_p / "transcript.srt", segments_to_srt(asr["segments"]))

    # 2) Diarization
    typer.echo("🧑‍🤝‍🧑 Diarizing (speaker clustering)…")
    diar = diarize_file(input, speakers=speakers)
    turns = attach_speakers(asr["segments"], diar)
    write_json(out_p / "speaker_turns.json", turns)
    write_speaker_md(out_p / "speaker_transcript.md", turns)

    # 3) LLM structuring → Notes
    typer.echo("🧠 Structuring notes with LLM…")
    notes = structure_notes(turns)
    write_json(out_p / "notes.json", notes)
    write_notes_md(out_p / "notes.md", notes)

    typer.echo(f"✅ Done → {out_p.resolve()}")
    emitted = [
        "transcript.txt",
        "transcript.json",
        "transcript.srt" if srt else None,
        "speaker_turns.json",
        "speaker_transcript.md",
        "notes.json",
        "notes.md",
    ]
    for f in filter(None, emitted):
        typer.echo(f"   - {f}")

if __name__ == "__main__":
    app()
