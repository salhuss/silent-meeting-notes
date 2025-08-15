# meeting_notes/summarize.py
from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime, timedelta
import os

def _next_friday_iso(today: datetime | None = None) -> str:
    """Return next Friday (or same Friday if today is Fri) as ISO YYYY-MM-DD."""
    today = today or datetime.now()
    weekday = today.weekday()  # Mon=0 ... Sun=6
    days_until_fri = (4 - weekday) % 7
    due = today + timedelta(days=days_until_fri or 7)  # prefer *next* Friday
    return due.strftime("%Y-%m-%d")

def _build_transcript(turns: List[Dict[str, Any]], max_chars: int = 12000) -> str:
    """Join speaker-attributed turns into a single transcript string, clipped for safety."""
    parts: List[str] = []
    total = 0
    for t in turns:
        line = f"{t['speaker']}: {t['text']}".strip()
        if not line:
            continue
        if total + len(line) + 1 > max_chars:
            parts.append("\n...[truncated]...")
            break
        parts.append(line)
        total += len(line) + 1
    return "\n".join(parts)

def _owner_guess(turn: Dict[str, Any]) -> str:
    """Heuristic owner guess (use speaker label)."""
    return turn.get("speaker", "S1")

PROMPT_SYS = (
    "You are a concise meeting-notes assistant. "
    "Given a multi-speaker transcript, produce crisp, actionable notes."
)

PROMPT_USER_TMPL = """Transcript (speaker-tagged):

{transcript}

Return strict JSON with these fields:
- summary: array of 5–10 short bullets capturing key points.
- decisions: array of bullets with any decisions made (or empty).
- actions: array of objects with fields:
  - owner (string like S1/S2 based on who should act),
  - task (imperative verb phrase),
  - suggested_due_date (YYYY-MM-DD).

Rules:
- Be specific and non-repetitive.
- Infer owners from context; if unclear, pick the most relevant speaker.
- If no clear decisions/actions, return empty arrays.
"""

def structure_notes(turns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calls OpenAI to convert speaker turns into {summary, decisions, actions}.
    If OPENAI_API_KEY is not set or call fails, returns a deterministic placeholder.
    """
    transcript = _build_transcript(turns)
    due = _next_friday_iso()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Fallback placeholder (offline) so CLI still works
        actions = []
        if turns:
            actions = [
                {"owner": _owner_guess(turns[0]), "task": "Review transcript and confirm action items", "suggested_due_date": due}
            ]
        return {
            "summary": ["(Offline placeholder) Set OPENAI_API_KEY to enable LLM summarization."],
            "decisions": [],
            "actions": actions,
        }

    try:
        # OpenAI SDK v1
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        msg = [
            {"role": "system", "content": PROMPT_SYS},
            {"role": "user", "content": PROMPT_USER_TMPL.format(transcript=transcript)},
        ]

        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=msg,
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        obj = resp.choices[0].message  # SDK returns .message
        # Some SDKs expose parsed JSON via .parsed; otherwise parse content
        parsed = getattr(obj, "parsed", None)
        if parsed is not None:
            notes = parsed
        else:
            import json
            notes = json.loads(obj.content)

        # Ensure due dates exist; add if missing
        for a in notes.get("actions", []) or []:
            a.setdefault("suggested_due_date", due)
            a.setdefault("owner", "S1")
        return notes

    except Exception as e:
        # Safe fallback so pipeline doesn't crash
        return {
            "summary": ["(LLM error) Could not generate notes.", f"Reason: {type(e).__name__}"],
            "decisions": [],
            "actions": [{"owner": "S1", "task": "Retry LLM summarization", "suggested_due_date": due}],
        }
