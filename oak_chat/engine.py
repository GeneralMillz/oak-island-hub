# oak_chat/engine.py


from typing import Dict, Any
from oak_chat.router import route_query
from oak_chat.prompt_template import build_prompt
import openai
import logging

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def call_llm(prompt: str) -> str:
    """
    Call the LLM with the given prompt. Adds logging and error handling.
    """
    logger.info("Calling LLM with prompt of length %d", len(prompt))
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are the Oak Island Research Assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        content = response["choices"][0]["message"]["content"]
        logger.debug("LLM response received (length %d)", len(content))
        return content
    except Exception as exc:
        logger.exception("Error calling LLM: %s", exc)
        raise



def answer_query(user_query: str) -> Dict[str, Any]:
    """
    End-to-end chatbot engine:
    - route the query
    - build a prompt
    - call the LLM
    - return structured result
    Adds logging and robust orchestration.
    """
    logger.info("Answering user query: %r", user_query)
    try:
        routed = route_query(user_query)
        logger.debug("Routing result: %r", routed)
        prompt = build_prompt(user_query, routed)
        logger.debug("Prompt built (length %d)", len(prompt))
        answer = call_llm(prompt)
        logger.info("LLM answer generated (length %d)", len(answer))
        return {
            "query": user_query,
            "route": routed,
            "prompt": prompt,
            "answer": answer,
        }
    except Exception as exc:
        logger.exception("Error in answer_query pipeline: %s", exc)
        return {
            "query": user_query,
            "route": None,
            "prompt": None,
            "answer": None,
            "error": str(exc),
        }
