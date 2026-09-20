from abc import ABC, abstractmethod
from typing import List
from app.core.config import settings
from app.core.logging import logger


class BaseEmbeddingService(ABC):
    """
    Abstract interface for generating vector embeddings.
    """

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        pass


class SentenceTransformerEmbeddingService(BaseEmbeddingService):
    """
    Local Embedding Service using SentenceTransformers.
    """
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name
        logger.info(f"Initializing SentenceTransformer model: {model_name}")
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        if not query:
            return [0.0] * 384
        embedding = self.model.encode(query, convert_to_numpy=True)
        return embedding.tolist()


class GeminiEmbeddingService(BaseEmbeddingService):
    """
    Google GenAI Embedding Service.
    """
    def __init__(self, api_key: str = settings.GEMINI_API_KEY):
        import google.generativeai as genai
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiEmbeddingService")
        genai.configure(api_key=api_key)
        self.genai = genai
        self.model = "models/embedding-001"

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        results = []
        for text in texts:
            res = self.genai.embed_content(model=self.model, content=text, task_type="retrieval_document")
            results.append(res["embedding"])
        return results

    def embed_query(self, query: str) -> List[float]:
        res = self.genai.embed_content(model=self.model, content=query, task_type="retrieval_query")
        return res["embedding"]


class OpenAIEmbeddingService(BaseEmbeddingService):
    """
    OpenAI Embedding Service.
    """
    def __init__(self, api_key: str = settings.OPENAI_API_KEY):
        from openai import OpenAI
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAIEmbeddingService")
        self.client = OpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        res = self.client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in res.data]

    def embed_query(self, query: str) -> List[float]:
        res = self.client.embeddings.create(input=[query], model=self.model)
        return res.data[0].embedding


def get_embedding_service() -> BaseEmbeddingService:
    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "gemini" and settings.GEMINI_API_KEY:
        try:
            return GeminiEmbeddingService()
        except Exception as e:
            logger.warning(f"Failed initializing Gemini embeddings: {e}. Falling back to SentenceTransformers.")
    elif provider == "openai" and settings.OPENAI_API_KEY:
        try:
            return OpenAIEmbeddingService()
        except Exception as e:
            logger.warning(f"Failed initializing OpenAI embeddings: {e}. Falling back to SentenceTransformers.")

    return SentenceTransformerEmbeddingService()


embedding_service = get_embedding_service()
