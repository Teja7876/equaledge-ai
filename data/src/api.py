from fastapi import APIRouter
from pydantic import BaseModel, Field
import logging
from typing import Any, Dict, Callable

# ------------------------------------------------
# Router
# ------------------------------------------------

router = APIRouter(tags=["EqualEdge Legal AI"])

# ------------------------------------------------
# Logging
# ------------------------------------------------

logger = logging.getLogger("equaledge.api")

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.setLevel(logging.INFO)

# ------------------------------------------------
# Lazy Engine Loader
# ------------------------------------------------

_engine: Callable | None = None


def get_engine() -> Callable:
    """
    Lazy-load the RPwD legal engine.
    Prevents Render startup failures if
    heavy dependencies are present.
    """

    global _engine

    if _engine is None:

        try:
            from src.services.rpwd_engine import generate_rpwd_answer

            _engine = generate_rpwd_answer

            logger.info("RPwD engine initialized successfully")

        except Exception as e:

            logger.exception("RPwD engine initialization failed")

            raise RuntimeError(
                f"AI engine initialization failed: {str(e)}"
            ) from e

    return _engine


# ------------------------------------------------
# Request Model
# ------------------------------------------------

class Question(BaseModel):
    question: str = Field(
        ...,
        min_length=2,
        description="User legal question"
    )


# ------------------------------------------------
# Question Normalization
# ------------------------------------------------

def normalize_question(text: str) -> str:
    """
    Normalize user questions to improve
    deterministic legal mapping.
    """

    text = text.lower().strip()

    replacements = {
        "pwd": "persons with disabilities",
        "disabled": "persons with disabilities",
        "handicapped": "persons with disabilities",
        "blind": "visual impairment",
        "visually impaired": "visual impairment",
        "quota": "reservation",
        "job quota": "employment reservation",
        "govt job": "government employment",
        "government job": "government employment",
        "college quota": "education reservation",
        "school quota": "education reservation",
        "job reservation": "employment reservation",
    }

    for key, value in replacements.items():
        if key in text:
            text = text.replace(key, value)

    return text


# ------------------------------------------------
# Response Formatter
# ------------------------------------------------

def format_response(result: Any) -> Dict[str, Any]:
    """
    Ensure consistent API response format
    for WordPress and Cloudflare worker.
    """

    if isinstance(result, dict):

        response: Dict[str, Any] = {
            "status": "success"
        }

        response.update(result)

        return response

    return {
        "status": "success",
        "answer": str(result)
    }


# ------------------------------------------------
# API Endpoint
# ------------------------------------------------

@router.post("/ask")
async def ask(q: Question):

    question = q.question.strip()

    if not question:

        return {
            "status": "error",
            "message": "Question cannot be empty"
        }

    try:

        logger.info("Question received: %s", question)

        normalized = normalize_question(question)

        logger.info("Normalized question: %s", normalized)

        engine = get_engine()

        result = engine(normalized)

        return format_response(result)

    except RuntimeError as exc:

        logger.error("Engine startup failure")

        return {
            "status": "error",
            "message": str(exc)
        }

    except Exception as exc:

        logger.exception("AI processing failure")

        return {
            "status": "error",
            "message": "EqualEdge AI encountered an internal processing error",
            "details": str(exc)
        }