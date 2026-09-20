import time
from typing import List, Tuple, Dict, Any, Optional
from app.models.chunk import Chunk
from app.models.api import SourceCitation, ChatMessage, QueryResponse
from app.core.config import settings
from app.core.logging import logger


class GroundedGenerator:
    """
    Grounded Multimodal Generator producing accurate, hallucination-free answers
    strictly bound to retrieved document context with verifiable source citations.
    """

    def __init__(self):
        self.provider = settings.DEFAULT_LLM_PROVIDER.lower()
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY

    def generate_answer(
        self,
        question: str,
        retrieved_chunks: List[Tuple[Chunk, float]],
        chat_history: Optional[List[ChatMessage]] = None,
        query_intent: Optional[str] = None
    ) -> QueryResponse:
        start_gen = time.time()

        if not retrieved_chunks:
            return QueryResponse(
                question=question,
                answer="The retrieved documents do not contain enough information to answer this question.",
                sources=[],
                retrieval_time_ms=0.0,
                generation_time_ms=round((time.time() - start_gen) * 1000, 2),
                query_intent=query_intent
            )

        # 1. Format Context & Sources
        context_blocks = []
        citations: List[SourceCitation] = []

        for idx, (chunk, score) in enumerate(retrieved_chunks):
            ref_id = f"[{idx+1}]"
            block = (
                f"Source {ref_id}:\n"
                f"Document: {chunk.metadata.file_name}\n"
                f"Page: {chunk.metadata.page_number}\n"
                f"Section: {chunk.metadata.section or 'N/A'}\n"
                f"Element Type: {chunk.metadata.element_type.value}\n"
                f"Content:\n{chunk.content}\n"
            )
            context_blocks.append(block)

            citations.append(SourceCitation(
                document_id=chunk.metadata.document_id,
                document_name=chunk.metadata.file_name,
                page_number=chunk.metadata.page_number,
                section=chunk.metadata.section,
                element_type=chunk.metadata.element_type.value,
                snippet=chunk.content[:200] + "...",
                gdrive_url=chunk.metadata.gdrive_url,
                relevance_score=round(score, 4)
            ))

        full_context_str = "\n---\n".join(context_blocks)

        # 2. Build Grounded System Prompt
        system_prompt = (
            "You are a Support Copilot. Your highest priority is accuracy, brevity, and extreme clarity.\n"
            "STRICT RULES:\n"
            "1. Base your answer ONLY on the provided RETRIEVED DOCUMENT CONTEXT below.\n"
            "2. Do NOT use outside knowledge, assume unstated facts, or hallucinate.\n"
            "3. Format your response in a minimal number of concise single-line bullets (NO ** bold asterisks, NO multi-paragraph quote dumps).\n"
            "4. Clearly cite your sources at the end of each bullet point using reference tags [1], [2].\n"
            "5. If context is insufficient, state: 'The retrieved documents do not contain enough information to answer this question.'\n\n"
            f"RETRIEVED DOCUMENT CONTEXT:\n{full_context_str}\n"
        )

        # Build conversation prompt
        user_prompt = f"Question: {question}\n\nPlease provide a concise, minimal-line answer with inline citations [1], [2]:"

        answer_text = ""
        # Validate API key format (Standard Google AI Studio keys start with 'AIzaSy')
        is_valid_gemini_key = bool(self.gemini_key and self.gemini_key.startswith("AIzaSy"))
        is_valid_openai_key = bool(self.openai_key and self.openai_key.startswith("sk-"))

        if self.provider == "gemini" and is_valid_gemini_key:
            answer_text = self._call_with_timeout(lambda: self._call_gemini(system_prompt, user_prompt, chat_history), timeout_sec=3.0)
            if not answer_text:
                answer_text = self._synthesize_fallback(question, retrieved_chunks)
        elif self.provider == "openai" and is_valid_openai_key:
            answer_text = self._call_with_timeout(lambda: self._call_openai(system_prompt, user_prompt, chat_history), timeout_sec=3.0)
            if not answer_text:
                answer_text = self._synthesize_fallback(question, retrieved_chunks)
        else:
            # High-performance local/fallback grounded synthesis (<10ms)
            answer_text = self._synthesize_fallback(question, retrieved_chunks)

        gen_time = round((time.time() - start_gen) * 1000, 2)

        return QueryResponse(
            question=question,
            answer=answer_text.strip(),
            sources=citations,
            retrieval_time_ms=0.0,
            generation_time_ms=gen_time,
            query_intent=query_intent
        )

    def _call_with_timeout(self, func, timeout_sec: float = 3.0) -> Optional[str]:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func)
            try:
                return future.result(timeout=timeout_sec)
            except concurrent.futures.TimeoutError:
                logger.warning(f"External LLM API call timed out after {timeout_sec}s. Using fast local synthesis.")
                return None
            except Exception as e:
                logger.warning(f"External LLM API call error: {e}. Using fast local synthesis.")
                return None

    def _call_gemini(self, system_prompt: str, user_prompt: str, chat_history: Optional[List[ChatMessage]]) -> str:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)

            messages = []
            if chat_history:
                for msg in chat_history[-4:]:
                    role = "user" if msg.role == "user" else "model"
                    messages.append({"role": role, "parts": [msg.content]})

            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}. Falling back to synthesis.")
            return self._synthesize_fallback(user_prompt, [])

    def _call_openai(self, system_prompt: str, user_prompt: str, chat_history: Optional[List[ChatMessage]]) -> str:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)
            messages = [{"role": "system", "content": system_prompt}]

            if chat_history:
                for msg in chat_history[-4:]:
                    messages.append({"role": msg.role, "content": msg.content})

            messages.append({"role": "user", "content": user_prompt})
            response = client.chat.completions.create(model=settings.OPENAI_MODEL, messages=messages, timeout=3.0)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}. Falling back to synthesis.")
            return self._synthesize_fallback(user_prompt, [])

    def _synthesize_fallback(self, question: str, retrieved_chunks: List[Tuple[Chunk, float]]) -> str:
        """Compact, minimal-line synthesis with complete, untruncated sentences."""
        if not retrieved_chunks:
            return "The retrieved documents do not contain enough information to answer this question."

        import re

        def clean_line(text: str) -> str:
            cleaned = re.sub(r'#{1,6}\s*', '', text)
            cleaned = re.sub(r'\*+', '', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            return cleaned

        bullet_lines = []
        source_refs = []

        for idx, (c, score) in enumerate(retrieved_chunks[:3]):
            ref = f"[{idx+1}]"
            doc_name = c.metadata.file_name
            pg = c.metadata.page_number
            
            cleaned = clean_line(c.content)
            # Extract complete sentences cleanly without truncation
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned) if s.strip()]
            if sentences:
                summary_text = sentences[0]
                if len(sentences) > 1 and len(summary_text) < 120:
                    summary_text += " " + sentences[1]
            else:
                summary_text = cleaned

            bullet_lines.append(f"• {summary_text} {ref}")
            source_refs.append(f"{doc_name} (p.{pg})")

        sources_str = ", ".join(source_refs)
        return "\n".join(bullet_lines) + f"\n\nSources: {sources_str}"


generator = GroundedGenerator()
