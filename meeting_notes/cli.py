import typer
from pathlib import Path

app = typer.Typer(help="Silent Meeting Notes CLI")

@app.command()
def main(
    input: str = typer.Argument(None, help="Path to audio file (wav/mp3/m4a)"),
    live: bool = typer.Option(False, "--live", help="Record from mic (MVP: placeholder)"),
    speakers: str = typer.Option("2-4", help="Speaker cluster range, e.g. '2-5'"),
    out: str = typer.Option("out", help="Output directory"),
):
    """
    MVP scaffold: just sets up folders and prints what would run.
    Next steps: wire in ASR, diarization, LLM structuring, and exporters.
    """
    out_p = Path(out)
    out_p.mkdir(parents=True, exist_ok=True)
    typer.echo("🔧 Silent Meeting Notes scaffold")
    typer.echo(f"Input: {input or '[live mic]'}")
    typer.echo(f"Speakers: {speakers}")
    typer.echo(f"Output dir: {out_p.resolve()}")
    # TODO: implement: load_audio -> transcribe -> diarize -> structure -> export
    # For now, create placeholder files so the CLI 'does something'.
    (out_p / "notes.md").write_text("# Notes\n\n(placeholder; coming soon)\n")
    (out_p / "notes.json").write_text('{"status":"placeholder"}\n')
    typer.echo("✅ Created placeholder notes.md and notes.json")

if __name__ == "__main__":
    app()
