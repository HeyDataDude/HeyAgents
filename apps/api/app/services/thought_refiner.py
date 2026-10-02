"""Thought Refiner (spec §7).

Converts messy speech into a useful, structured thought. It does NOT advise the user. It:
  - preserves intended meaning, uncertainty, questions, speculation, distinctions, key wording;
  - removes filler words, accidental repetition, speech artifacts, verbal noise;
  - NEVER turns uncertain statements into confident facts.

In mock mode this is a careful rule-based implementation. In live mode it uses an LLM with a strict
system prompt + JSON schema; the output is validated with Pydantic (`RefinedThought`).
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from app.core.enums import ThoughtType
from app.integrations.base import LLMMessage, LLMProvider

FILLERS = {
    "um", "uh", "er", "ah", "like", "you know", "i mean", "sort of", "kind of",
    "basically", "literally", "actually", "so yeah", "right",
}

UNCERTAINTY_MARKERS = (
    "maybe", "perhaps", "might", "could", "i think", "i guess", "possibly",
    "i don't know", "not sure", "i wonder", "seems",
)

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "to", "of", "in", "on", "for", "is", "are",
    "was", "were", "be", "been", "it", "that", "this", "there", "some", "just", "about",
    "they", "them", "their", "i", "me", "my", "we", "you", "he", "she", "do", "does", "not",
    "with", "as", "at", "by", "from", "so", "too", "also", "more", "than", "then", "maybe",
    "like", "part", "thing", "things", "today", "same", "genuinely", "broader", "obvious",
}


class RefinedThought(BaseModel):
    clean_transcript: str
    title: str
    summary: str
    thought_type: ThoughtType = ThoughtType.NOTE
    topics: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    ideas: list[str] = Field(default_factory=list)
    possible_actions: list[str] = Field(default_factory=list)
    importance: int = 3
    urgency: int = 2


REFINER_SYSTEM = (
    "You are the Thought Refiner for Council. Convert messy spoken input into a clean, structured "
    "thought. Preserve meaning, uncertainty, questions, speculation and distinctions. Remove filler "
    "words and repetition. NEVER convert uncertain statements into confident facts. Return strict "
    "JSON matching the RefinedThought schema."
)


class ThoughtRefinerService:
    def __init__(self, llm: LLMProvider, *, mock: bool):
        self._llm = llm
        self._mock = mock

    async def refine(self, raw_transcript: str) -> RefinedThought:
        if self._mock:
            return self._refine_rule_based(raw_transcript)
        return await self._refine_llm(raw_transcript)

    async def _refine_llm(self, raw: str) -> RefinedThought:
        messages = [
            LLMMessage("system", REFINER_SYSTEM),
            LLMMessage("user", f"Raw transcript:\n{raw}\n\nReturn JSON."),
        ]
        try:
            data = await self._llm.complete_json(messages)
            return RefinedThought.model_validate(data)
        except Exception:
            # Never lose the thought because refinement failed — fall back to rule-based.
            return self._refine_rule_based(raw)

    # ── Rule-based (mock) refinement ──────────────────────────────────────────
    def _refine_rule_based(self, raw: str) -> RefinedThought:
        clean = self._clean(raw)
        sentences = _sentences(clean)
        questions = [s for s in sentences if s.strip().endswith("?") or _looks_like_question(s)]
        ideas = [s for s in sentences if _mentions(s, ("idea", "could be", "what if", "content"))]
        actions = self._actions(sentences)
        topics = self._topics(clean)
        summary = sentences[0] if sentences else clean[:160]
        title = self._title(summary)
        ttype = self._classify(clean, questions, ideas)
        importance = 4 if _mentions(clean, ("important", "deadline", "urgent")) else 3
        urgency = 4 if _mentions(clean, ("today", "now", "asap", "deadline")) else 2
        return RefinedThought(
            clean_transcript=clean,
            title=title,
            summary=summary,
            thought_type=ttype,
            topics=topics,
            entities=self._entities(raw),
            questions=questions,
            ideas=ideas,
            possible_actions=actions,
            importance=importance,
            urgency=urgency,
        )

    def _clean(self, raw: str) -> str:
        text = raw.strip()
        # Remove filler phrases (longest first) while preserving uncertainty words.
        for filler in sorted(FILLERS, key=len, reverse=True):
            if filler in UNCERTAINTY_MARKERS:
                continue
            text = re.sub(rf"\b{re.escape(filler)}\b", "", text, flags=re.IGNORECASE)
        # Collapse accidental word repetition ("the the").
        text = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
        text = re.sub(r"\s{2,}", " ", text)
        text = re.sub(r"\s+([.,?!])", r"\1", text)
        # Collapse punctuation orphaned by filler removal (", ," / ",,").
        text = re.sub(r"(\s*,\s*){2,}", ", ", text)
        text = re.sub(r",\s*([.?!])", r"\1", text)
        text = re.sub(r"\s{2,}", " ", text)
        # Capitalize sentence starts.
        text = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
        return text.strip(" ,")

    def _topics(self, text: str) -> list[str]:
        words = re.findall(r"[a-zA-Z]{4,}", text.lower())
        freq: dict[str, int] = {}
        for w in words:
            if w in STOPWORDS:
                continue
            freq[w] = freq.get(w, 0) + 1
        ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
        return [w for w, _ in ranked[:6]]

    def _entities(self, raw: str) -> list[str]:
        # Proper-noun-ish tokens (capitalized, not sentence start) — conservative.
        found = re.findall(r"(?<!^)(?<![.!?]\s)\b([A-Z][a-zA-Z]{2,})\b", raw)
        seen: list[str] = []
        for f in found:
            if f not in seen:
                seen.append(f)
        return seen[:8]

    def _actions(self, sentences: list[str]) -> list[str]:
        verbs = ("write", "build", "research", "call", "email", "draft", "make", "create", "plan",
                 "explore", "investigate", "record", "publish", "schedule")
        out = []
        for s in sentences:
            if _mentions(s, verbs) or _mentions(s, ("could be", "should", "need to")):
                out.append(s.strip())
        return out[:5]

    def _title(self, summary: str) -> str:
        text = summary.strip()
        if not text:
            return "Untitled thought"
        if len(text) <= 60:
            return text
        truncated = text[:60].rsplit(" ", 1)[0].strip()
        return (truncated or text[:60].strip()) + "…"

    def _classify(self, text: str, questions, ideas) -> ThoughtType:
        if questions and len(questions) >= 2:
            return ThoughtType.QUESTION
        if ideas:
            return ThoughtType.IDEA
        if _mentions(text, ("i should", "need to", "todo", "task")):
            return ThoughtType.TASK
        if _mentions(text, ("i decided", "decision", "going with")):
            return ThoughtType.DECISION
        if _mentions(text, ("i was thinking", "i feel", "i realized")):
            return ThoughtType.REFLECTION
        return ThoughtType.OBSERVATION


# ── helpers ──────────────────────────────────────────────────────────────────────
def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _looks_like_question(s: str) -> bool:
    return bool(re.match(r"^\s*(why|how|what|when|where|who|should|could|is|are|does|do)\b", s, re.I))


def _mentions(text: str, needles) -> bool:
    low = text.lower()
    return any(n in low for n in needles)
