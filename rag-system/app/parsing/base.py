from abc import ABC, abstractmethod
from app.models.document import Document


class BaseDocumentParser(ABC):
    """
    Abstract Base Class for document parsers.
    """

    @abstractmethod
    def parse(self, file_path: str, file_id: str, file_name: str, gdrive_url: str = "") -> Document:
        """
        Parse document file into unified Document structure.
        """
        pass
