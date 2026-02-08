# oak_chat/prompt_template.py


from typing import Dict, Any, List, Optional
import logging

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


SYSTEM_PROMPT = """You are the Oak Island Research Assistant.

You have access to a structured SQLite-backed knowledge base of:
- episodes (season, episode, title)
- events (timestamped actions and discoveries)
- theories (explanations, hypotheses, interpretations)
- measurements (depths, distances, dimensions)
- artifacts (physical finds)
- transcripts (dialogue and narration)

You must:
- Answer ONLY using the data provided in the "context" section.
- Prefer concrete details: seasons, episodes, timestamps, names, locations.
- When possible, cite season and episode like: (S3E4).
- If the data is incomplete or ambiguous, say so explicitly.
- Do NOT invent facts or speculate beyond the provided context.
"""



def build_context_block(routed: Dict[str, Any]) -> str:
    """
    Turn router output into a textual context block for the LLM.
    Adds robust handling for missing/invalid data and logs context shaping.
    """
    t = routed.get("type", "unknown")
    term = routed.get("term") or routed.get("person") or ""

    lines: List[str] = [f"Query type: {t}", f"Search term / focus: {term}", "", "Context data:"]

    def add_rows(label: str, rows: Optional[List[Dict[str, Any]]]):
        if not rows:
            logger.debug("No rows for label '%s'", label)
            return
        lines.append(f"\n[{label}]")
        for r in rows[:50]:
            parts = []
            if isinstance(r, dict):
                if "season" in r and "episode" in r:
                    parts.append(f"S{r.get('season')}E{r.get('episode')}")
                if "title" in r and r.get("title"):
                    parts.append(str(r["title"]))
                if "timestamp" in r and r.get("timestamp"):
                    parts.append(f"@{r['timestamp']}")
                if "event_type" in r and r.get("event_type"):
                    parts.append(f"({r['event_type']})")
                text = r.get("text", "")
                snippet = text if isinstance(text, str) and len(text) <= 260 else (text[:257] + "..." if isinstance(text, str) else "")
                parts.append(f": {snippet}")
                lines.append(" - " + " ".join(parts))
            else:
                logger.warning("Row is not a dict: %r", r)
                lines.append(f" - [Malformed row: {r}]")

    # Shape context based on query type
    if t in ("theories_by_term", "theories"):
        add_rows("Theories", routed.get("results", []))
    elif t in ("episodes_by_person", "episodes_by_term"):
        add_rows("Episodes", routed.get("results", []))
    elif t == "events":
        add_rows("Events", routed.get("results", []))
    elif t == "transcripts":
        add_rows("Transcript lines", routed.get("results", []))
    elif t == "timeline":
        add_rows("Timeline entries", routed.get("results", []))
    elif t == "location_summary":
        res = routed.get("results", {})
        add_rows("Events", res.get("events", []))
        add_rows("Theories", res.get("theories", []))
        add_rows("Episodes", res.get("episodes", []))
    elif t == "fallback":
        res = routed.get("results", {})
        add_rows("Events", res.get("events", []))
        add_rows("Theories", res.get("theories", []))
        add_rows("Transcripts", res.get("transcripts", []))
    elif t == "error":
        error_msg = routed.get("error", "Unknown error")
        lines.append(f"\n[Error]\n - {error_msg}")
    else:
        logger.warning("Unknown query type for context block: %r", t)
        lines.append(f"\n[Unknown query type: {t}]")

    return "\n".join(lines)



def build_prompt(user_query: str, routed: Dict[str, Any]) -> str:
    """
    Build the full prompt for the LLM, including the system prompt, user question, and context block.
    """
    context_block = build_context_block(routed)
    return f"""{SYSTEM_PROMPT}

User question:
{user_query}

{context_block}

Now, answer the user's question using ONLY the context above.
Be concise but clear. If relevant, reference episodes as (SxEy).
If the answer is uncertain or partial, say so explicitly."""
