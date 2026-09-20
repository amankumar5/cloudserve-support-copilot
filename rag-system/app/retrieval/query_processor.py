import re
from typing import List, Dict, Any, Optional
from app.models.api import ChatMessage
from app.core.config import settings
from app.core.logging import logger


class QueryProcessor:
    """
    Query Intent Classifier and Contextual Chat Query Rewriter.
    """

    TABLE_KEYWORDS = ["revenue", "growth", "sales", "highest", "lowest", "total", "percentage", "table", "matrix", "product a", "product b", "compare", "rate", "cost"]
    DIAGRAM_KEYWORDS = ["architecture", "flow", "flowchart", "diagram", "component", "service", "system", "gateway", "database", "connection", "process", "screenshot", "layout"]
    LOOKUP_KEYWORDS = ["error code", "id", "version", "clause", "section", "specific", "exact"]

    def classify_intent(self, question: str) -> str:
        q_lower = question.lower()

        t_count = sum(1 for k in self.TABLE_KEYWORDS if k in q_lower)
        d_count = sum(1 for k in self.DIAGRAM_KEYWORDS if k in q_lower)
        l_count = sum(1 for k in self.LOOKUP_KEYWORDS if k in q_lower)

        if l_count > 0 and (t_count == 0 and d_count == 0):
            return "exact_lookup"
        if t_count > d_count and t_count > 0:
            return "table_query"
        if d_count > t_count and d_count > 0:
            return "diagram_query"

        return "text_query"

    def rewrite_query_with_history(self, question: str, chat_history: Optional[List[ChatMessage]]) -> str:
        """
        Rewrite follow-up questions using recent chat history.
        e.g., 'What database does it use?' -> 'What database does Payment Service use?'
        """
        if not chat_history:
            return question

        # Check if question has pronouns / ambiguous references ('it', 'this', 'that', 'they')
        pronouns = ["it", "its", "this", "that", "they", "them", "these", "those"]
        tokens = re.findall(r"\b\w+\b", question.lower())
        has_pronoun = any(p in tokens for p in pronouns)

        if not has_pronoun:
            return question

        # Extract last assistant or user message context
        context_subjects = []
        for msg in reversed(chat_history[-4:]):
            # Simple keyword extraction from previous assistant message
            words = [w for w in re.findall(r"\b[A-Z][a-zA-Z0-9_]+\b", msg.content) if len(w) > 2]
            context_subjects.extend(words)

        if context_subjects:
            subject = context_subjects[0]
            rewritten = f"{question} (context entity: {subject})"
            logger.info(f"Rewrote query '{question}' -> '{rewritten}'")
            return rewritten

        return question


query_processor = QueryProcessor()
