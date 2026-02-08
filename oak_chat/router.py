# oak_chat/router.py

from typing import Dict, Any
from oak_chat.queries import (
    search_events_text,
    search_theories_text,
    search_transcripts_text,
    find_episodes_mentioning_person,
    find_episodes_mentioning_term,
    timeline_for_term,
    summarize_location_seed,
    theories_mentioning_term,
)

import logging

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def route_query(user_query: str) -> Dict[str, Any]:
    """
    Interpret a natural-language question and route it to the correct query function(s).
    Returns a structured dict for the chatbot to summarize.
    """

    logger.info("Routing user query: %r", user_query)
    q = user_query.lower().strip()

    try:
        # ---------- TIMELINE ----------
        if "timeline" in q:
            # e.g., "timeline for smith's cove"
            term = q.replace("timeline", "").replace("for", "").strip()
            logger.debug("Timeline query detected. Term: '%s'", term)
            data = timeline_for_term(term)
            return {
                "type": "timeline",
                "term": term,
                "results": data,
            }

        # ---------- SUMMARIZE LOCATION ----------
        if "summarize" in q or "summary" in q:
            # e.g., "summarize the money pit"
            term = q.replace("summarize", "").replace("summary", "").strip()
            logger.debug("Location summary query detected. Term: '%s'", term)
            data = summarize_location_seed(term)
            return {
                "type": "location_summary",
                "term": term,
                "results": data,
            }

        # ---------- THEORIES ----------
        if "theories" in q or "theory" in q:
            # e.g., "what theories mention treasure?"
            if "mention" in q:
                # extract term after "mention"
                parts = q.split("mention")
                term = parts[-1].strip()
                logger.debug("Theories mentioning term query. Term: '%s'", term)
                data = theories_mentioning_term(term)
                return {
                    "type": "theories_by_term",
                    "term": term,
                    "results": data,
                }

        # ---------- EPISODES MENTIONING PERSON ----------
        if "episodes" in q and ("mention" in q or "featuring" in q or "with" in q):
            # e.g., "which episodes mention zena halpern?"
            parts = q.split("mention") if "mention" in q else q.split("with")
            term = parts[-1].strip()
            logger.debug("Episodes mentioning person query. Person: '%s'", term)
            data = find_episodes_mentioning_person(term)
            return {
                "type": "episodes_by_person",
                "person": term,
                "results": data,
            }

        # ---------- GENERIC EPISODE SEARCH ----------
        if "episodes" in q and "mention" in q:
            term = q.split("mention")[-1].strip()
            logger.debug("Episodes mentioning term query. Term: '%s'", term)
            data = find_episodes_mentioning_term(term)
            return {
                "type": "episodes_by_term",
                "term": term,
                "results": data,
            }

        # ---------- EVENT SEARCH ----------
        if "event" in q or "events" in q:
            # e.g., "events about the money pit"
            term = q.replace("events", "").replace("event", "").strip()
            logger.debug("Events search query. Term: '%s'", term)
            data = search_events_text(term)
            return {
                "type": "events",
                "term": term,
                "results": data,
            }

        # ---------- TRANSCRIPT SEARCH ----------
        if "transcript" in q or "dialogue" in q or "line" in q:
            term = q.replace("transcript", "").replace("dialogue", "").replace("line", "").strip()
            logger.debug("Transcripts search query. Term: '%s'", term)
            data = search_transcripts_text(term)
            return {
                "type": "transcripts",
                "term": term,
                "results": data,
            }

        # ---------- THEORY SEARCH ----------
        if "treasure" in q or "templar" in q or "theory" in q:
            # fallback: treat as theory search
            logger.debug("Fallback theory search. Query: '%s'", q)
            data = search_theories_text(q)
            return {
                "type": "theories",
                "term": q,
                "results": data,
            }

        # ---------- FALLBACK: SEARCH EVERYTHING ----------
        # If we can't classify the question, search all text sources.
        logger.debug("Fallback: search all sources for query: '%s'", q)
        events = search_events_text(q)
        theories = search_theories_text(q)
        transcripts = search_transcripts_text(q)

        return {
            "type": "fallback",
            "term": q,
            "results": {
                "events": events,
                "theories": theories,
                "transcripts": transcripts,
            },
        }
    except Exception as exc:
        logger.exception("Error routing query: %r", user_query)
        return {
            "type": "error",
            "term": user_query,
            "error": str(exc),
        }

    q = user_query.lower().strip()

    # ---------- TIMELINE ----------
    if "timeline" in q:
        # e.g., "timeline for smith's cove"
        term = q.replace("timeline", "").replace("for", "").strip()
        data = timeline_for_term(term)
        return {
            "type": "timeline",
            "term": term,
            "results": data,
        }

    # ---------- SUMMARIZE LOCATION ----------
    if "summarize" in q or "summary" in q:
        # e.g., "summarize the money pit"
        term = q.replace("summarize", "").replace("summary", "").strip()
        data = summarize_location_seed(term)
        return {
            "type": "location_summary",
            "term": term,
            "results": data,
        }

    # ---------- THEORIES ----------
    if "theories" in q or "theory" in q:
        # e.g., "what theories mention treasure?"
        if "mention" in q:
            # extract term after "mention"
            parts = q.split("mention")
            term = parts[-1].strip()
            data = theories_mentioning_term(term)
            return {
                "type": "theories_by_term",
                "term": term,
                "results": data,
            }

    # ---------- EPISODES MENTIONING PERSON ----------
    if "episodes" in q and ("mention" in q or "featuring" in q or "with" in q):
        # e.g., "which episodes mention zena halpern?"
        parts = q.split("mention") if "mention" in q else q.split("with")
        term = parts[-1].strip()
        data = find_episodes_mentioning_person(term)
        return {
            "type": "episodes_by_person",
            "person": term,
            "results": data,
        }

    # ---------- GENERIC EPISODE SEARCH ----------
    if "episodes" in q and "mention" in q:
        term = q.split("mention")[-1].strip()
        data = find_episodes_mentioning_term(term)
        return {
            "type": "episodes_by_term",
            "term": term,
            "results": data,
        }

    # ---------- EVENT SEARCH ----------
    if "event" in q or "events" in q:
        # e.g., "events about the money pit"
        term = q.replace("events", "").replace("event", "").strip()
        data = search_events_text(term)
        return {
            "type": "events",
            "term": term,
            "results": data,
        }

    # ---------- TRANSCRIPT SEARCH ----------
    if "transcript" in q or "dialogue" in q or "line" in q:
        term = q.replace("transcript", "").replace("dialogue", "").replace("line", "").strip()
        data = search_transcripts_text(term)
        return {
            "type": "transcripts",
            "term": term,
            "results": data,
        }

    # ---------- THEORY SEARCH ----------
    if "treasure" in q or "templar" in q or "theory" in q:
        # fallback: treat as theory search
        data = search_theories_text(q)
        return {
            "type": "theories",
            "term": q,
            "results": data,
        }

    # ---------- FALLBACK: SEARCH EVERYTHING ----------
    # If we can't classify the question, search all text sources.
    events = search_events_text(q)
    theories = search_theories_text(q)
    transcripts = search_transcripts_text(q)

    return {
        "type": "fallback",
        "term": q,
        "results": {
            "events": events,
            "theories": theories,
            "transcripts": transcripts,
        },
    }
