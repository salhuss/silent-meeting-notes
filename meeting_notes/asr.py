# meeting_notes/asr.py
from typing import List, Dict, Optional
from faster_whisper import WhisperModel
from pathlib import Path
import os

def load_model(model_size: str = None, device: str = "auto", compute_type: str = "auto") -> WhisperModel:
    """
    model_size: one of tiny, base, small, medium, large-v3 (default via env)
    device: "cpu" or "cuda" or "auto"
    compute_type: "int8", "int8_float16", "float16", "float32", or "auto"
    """
    model_size = model_size or os.getenv("WHISPER_MODEL", "base")
    cache_dir = os.getenv("WHISPER_CACHE_DIR", None)
    return WhisperModel(model_size, device=device, compute_type=compute_type, download_root=cache_dir)

def transcribe_file(
    audio_path: str,
    model_size: Optional[str] = None,
    word_timestamps: bool = True,
    vad_filter: bool = True,
) -> Dict:
    """
    Returns:
      {
        "language": "en",
        "segments": [
          {"start": 0.12, "end": 2.34, "text": "Hello world", "words": [{"start":..., "end":..., "word":"Hello"}, ...]}
        ],
        "text": "full transcript ..."
      }
    """
    model = load_model(model_size=model_size)
    audio_path = str(Path(audio_path).expanduser().resolve())

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=vad_filter,
        word_timestamps=word_timestamps,
    )

    segs: List[Dict] = []
    full_text_parts: List[str] = []
    for s in segments:
        item = {
            "start": float(s.start) if s.start is not None else 0.0,
            "end": float(s.end) if s.end is not None else 0.0,
            "text": s.text.strip(),
        }
        if word_timestamps and getattr(s, "words", None):
            item["words"] = [
                {"start": float(w.start or 0.0), "end": float(w.end or 0.0), "word": w.word}
                for w in s.words
            ]
        segs.append(item)
        full_text_parts.append(item["text"])

    return {
        "language": info.language,
        "segments": segs,
        "text": " ".join(full_text_parts).strip()
    }
