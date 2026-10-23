import concurrent.futures
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from src.app.core.config import get_settings
from src.app.core.exceptions import LLMConfigurationError, LLMTimeoutError

logger = logging.getLogger(__name__)
settings = get_settings()

GROUNDING_SYSTEM_PROMPT = """You are InsightFlow AI, a precise, truthful, and evidence-grounded document assistant.
Your task is to answer the user's question STRICTLY and ONLY using the provided source context snippets.

RULES:
1. Grounding: Every statement in your answer must be supported by the provided context snippets.
2. Missing or Insufficient Evidence: If the provided context snippets do NOT contain sufficient factual evidence to answer the question, or if no snippets are provided, you MUST reply EXACTLY with:
"I do not have sufficient evidence in the provided documents to answer this question."
Do NOT fabricate, guess, or extrapolate facts.
3. Citations: When answering from the context, include specific in-text citations referencing the source document and page/section (e.g., "[financial_report.pdf, Page 1]" or "[architecture.docx, Section: Overview]").
4. Tone: Concise, professional, and directly addressing the user's inquiry.
"""


class BaseLLMProvider(ABC):
    """Abstract interface for LLM response generation."""

    @abstractmethod
    def generate_grounded_answer(self, question: str, context_blocks: List[str]) -> str:
        """Generates an answer grounded strictly in the provided context blocks."""
        pass


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini GenAI LLM Provider."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL

    def generate_grounded_answer(self, question: str, context_blocks: List[str]) -> str:
        if not self.api_key or self.api_key.startswith("mock_"):
            raise LLMConfigurationError(
                "GEMINI_API_KEY is not configured. Please provide a valid Gemini API key.",
                details={"provider": "gemini"},
            )

        context_text = "\n\n---\n\n".join(context_blocks)
        prompt = (
            f"{GROUNDING_SYSTEM_PROMPT}\n\n"
            f"SOURCE CONTEXT SNIPPETS:\n{context_text}\n\n"
            f"USER QUESTION: {question}\n\n"
            f"GROUNDED ANSWER:"
        )

        def _call_gemini():
            from google import genai

            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_call_gemini)
                answer = future.result(timeout=settings.LLM_TIMEOUT_SECONDS)
                return answer.strip()
        except concurrent.futures.TimeoutError:
            logger.error(f"Gemini LLM call timed out after {settings.LLM_TIMEOUT_SECONDS}s")
            raise LLMTimeoutError(
                f"LLM generation timed out after {settings.LLM_TIMEOUT_SECONDS} seconds.",
                details={"timeout_seconds": settings.LLM_TIMEOUT_SECONDS},
            )
        except Exception as e:
            logger.error(f"Gemini LLM generation failed: {e}", exc_info=True)
            raise


class MockLLMProvider(BaseLLMProvider):
    """Deterministic Mock LLM Provider used for automated testing and offline environments."""

    def generate_grounded_answer(self, question: str, context_blocks: List[str]) -> str:
        if not context_blocks:
            return "I do not have sufficient evidence in the provided documents to answer this question."

        q_lower = question.lower()
        matched_blocks = [b for b in context_blocks if any(word in b.lower() for word in q_lower.split() if len(word) > 3)]

        if not matched_blocks:
            return "I do not have sufficient evidence in the provided documents to answer this question."

        first_block = matched_blocks[0]
        lines = [line.strip() for line in first_block.split("\n") if line.strip() and not line.startswith("[")]
        
        # Pick the line specifically containing query keyword matches if possible
        matched_lines = [l for l in lines if any(w in l.lower() for w in q_lower.split() if len(w) > 3)]
        content_summary = matched_lines[0] if matched_lines else (lines[0] if lines else first_block[:120])

        # Extract citation breadcrumb if present
        citation_tag = ""
        if first_block.startswith("["):
            citation_tag = " " + first_block.split("]")[0] + "]"

        return f"Based on the provided records, {content_summary}.{citation_tag}"


def get_llm_provider() -> BaseLLMProvider:
    """Returns configured LLM provider instance."""
    provider = settings.LLM_PROVIDER.lower()
    if provider == "mock":
        return MockLLMProvider()
    return GeminiLLMProvider()
