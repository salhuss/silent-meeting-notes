# meeting_notes/diarize.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from resemblyzer import VoiceEncoder, preprocess_wav
from resemblyzer.hparams import sampling_rate as RZ_SR

WINDOW_S = 1.5
STEP_S = 0.5

@dataclass
class DiarSeg:
    start: float
    end: float
    spk: str  # "S1", "S2", ...

def _parse_range(r: str) -> Tuple[int, int]:
    if "-" in r:
        a, b = r.split("-", 1)
        return int(a), int(b)
    n = int(r)
    return (n, n)

def _best_k(partials: np.ndarray, kmin: int, kmax: int) -> int:
    if kmin == kmax:
        return kmin
    # guard for short audio
    if len(partials) < kmin:
        return max(2, min(kmax, len(partials))) if len(partials) >= 2 else 1
    best_k, best_score = kmin, -1.0
    X = partials
    for k in range(kmin, kmax + 1):
        try:
            labels = KMeans(n_clusters=k, n_init="auto", random_state=42).fit_predict(X)
            score = silhouette_score(X, labels) if k > 1 else -1.0
            if score > best_score:
                best_k, best_score = k, score
        except Exception:
            continue
    return best_k

def _merge_adjacent(labels: np.ndarray, times_s: np.ndarray) -> List[DiarSeg]:
    # times_s are window centers; build [center - WIN/2, center + WIN/2]
    segs: List[DiarSeg] = []
    if len(labels) == 0:
        return segs
    cur_label = labels[0]
    cur_start = float(times_s[0] - WINDOW_S/2)
    cur_end = float(times_s[0] + WINDOW_S/2)
    for i in range(1, len(labels)):
        lb = labels[i]
        s = float(times_s[i] - WINDOW_S/2)
        e = float(times_s[i] + WINDOW_S/2)
        # if same speaker and contiguous/overlapping, extend
        if lb == cur_label and s <= cur_end + STEP_S/2:
            cur_end = max(cur_end, e)
        else:
            segs.append(DiarSeg(start=max(0.0, cur_start), end=max(cur_start, cur_end), spk=f"S{int(cur_label)+1}"))
            cur_label, cur_start, cur_end = lb, s, e
    segs.append(DiarSeg(start=max(0.0, cur_start), end=max(cur_start, cur_end), spk=f"S{int(cur_label)+1}"))
    return segs

def diarize_file(audio_path: str, speakers: str = "2-4") -> List[DiarSeg]:
    """
    Returns a list of diarization segments: [{start, end, spk: "S1"}...]
    """
    ap = str(Path(audio_path).expanduser().resolve())
    wav = preprocess_wav(ap)  # re-samples to RZ_SR, mono, float32
    if len(wav) < RZ_SR * 0.5:
        return [DiarSeg(0.0, float(len(wav)/RZ_SR), "S1")]
    enc = VoiceEncoder()
    # Partial embeddings across the utterance
    _, partial_embeds, times_s = enc.embed_utterance(wav, return_partials=True, rate=STEP_S/WINDOW_S)
    partials = np.vstack(partial_embeds) if isinstance(partial_embeds, list) else partial_embeds
    times_s = np.array(times_s, dtype=float)
    if len(partials) == 0:
        return [DiarSeg(0.0, float(len(wav)/RZ_SR), "S1")]
    kmin, kmax = _parse_range(speakers)
    k = _best_k(partials, max(1, kmin), max(1, kmax))
    labels = KMeans(n_clusters=max(1, k), n_init="auto", random_state=42).fit_predict(partials)
    return _merge_adjacent(labels, times_s)

def _dominant_speaker_for_span(start: float, end: float, diar: List[DiarSeg]) -> str:
    # choose the speaker whose overlap with [start,end] is max
    best_spk, best_olap = "S1", 0.0
    for d in diar:
        ol = max(0.0, min(end, d.end) - max(start, d.start))
        if ol > best_olap:
            best_olap, best_spk = ol, d.spk
    return best_spk

def attach_speakers(asr_segments: List[Dict], diar: List[DiarSeg]) -> List[Dict]:
    """
    For each ASR segment (or word if available), attach a speaker label.
    Returns a list of 'turns' with merged consecutive same-speaker text.
    """
    words: List[Dict] = []
    for s in asr_segments:
        if "words" in s and s["words"]:
            for w in s["words"]:
                spk = _dominant_speaker_for_span(w["start"], w["end"], diar)
                words.append({"start": w["start"], "end": w["end"], "text": w["word"], "spk": spk})
        else:
            spk = _dominant_speaker_for_span(s["start"], s["end"], diar)
            words.append({"start": s["start"], "end": s["end"], "text": s["text"], "spk": spk})

    # Merge into turns
    turns: List[Dict] = []
    if not words:
        return turns
    cur_spk = words[0]["spk"]
    cur_start = words[0]["start"]
    cur_end = words[0]["end"]
    cur_tokens = [words[0]["text"]]

    for w in words[1:]:
        if w["spk"] == cur_spk and w["start"] <= cur_end + 0.6:  # small bridge
            cur_tokens.append(w["text"])
            cur_end = max(cur_end, w["end"])
        else:
            turns.append({"speaker": cur_spk, "start": cur_start, "end": cur_end, "text": " ".join(cur_tokens).strip()})
            cur_spk = w["spk"]; cur_start = w["start"]; cur_end = w["end"]; cur_tokens = [w["text"]]
    turns.append({"speaker": cur_spk, "start": cur_start, "end": cur_end, "text": " ".join(cur_tokens).strip()})
    return turns
