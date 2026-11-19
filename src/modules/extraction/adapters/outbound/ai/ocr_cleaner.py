"""Optional low-confidence OCR correction; the raw OCR reading remains authoritative."""
from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage


class LangChainOCRCleaner:
    def __init__(self, model: BaseChatModel):
        self.model = model

    def clean(self, raw_text: str) -> str:
        response = self.model.invoke([
            SystemMessage(content="Correct only obvious OCR character and spacing errors in this financial document transcription. Preserve all names, numbers, dates, tax IDs, currencies, line order, and uncertainty. Never add missing information. Return only corrected text. If uncertain, return the input unchanged."),
            HumanMessage(content=raw_text[:12_000]),
        ])
        if isinstance(response.content, str):
            return response.content.strip()
        return "\n".join(str(block.get("text", "")) for block in response.content if isinstance(block, dict) and block.get("type") == "text").strip()
