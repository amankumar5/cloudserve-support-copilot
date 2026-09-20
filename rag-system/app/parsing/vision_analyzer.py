import os
import json
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger


class VisionAnalyzer:
    """
    Vision Analyzer using Gemini Multimodal Vision model to understand architecture diagrams,
    flowcharts, graphs, screenshots, and visual technical illustrations.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL

    def analyze_image(self, image_path: str, context_caption: str = "") -> Dict[str, Any]:
        """
        Analyze diagram/image and return detailed semantic description and structure.
        """
        if not os.path.exists(image_path):
            return {"description": "Image file not found.", "components": [], "text_labels": []}

        if not self.api_key:
            return self._fallback_analysis(image_path, context_caption)

        try:
            import google.generativeai as genai
            from PIL import Image

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model_name)
            img = Image.open(image_path)

            prompt = f"""
You are an expert technical document visual analyzer.
Analyze this diagram/image in detail.
Context Caption: {context_caption}

Provide your analysis in JSON format with the following keys:
1. "description": A thorough, detailed semantic description of what this diagram/image shows, step-by-step connections, data flow, architecture components, or chart trends.
2. "diagram_type": Type of visual (e.g., "architecture_diagram", "flowchart", "bar_chart", "screenshot", "table_image", "general_image").
3. "components": List of key components/nodes/modules depicted.
4. "connections": List of relationships, arrows, or data flow paths (e.g. "User -> API Gateway -> Order Service").
5. "text_labels": List of exact text labels or values read from the image.

Ensure the output is strictly valid JSON.
"""

            response = model.generate_content([prompt, img])
            text_resp = response.text.strip()

            # Clean JSON formatting wrappers
            if text_resp.startswith("```json"):
                text_resp = text_resp[7:]
            if text_resp.startswith("```"):
                text_resp = text_resp[3:]
            if text_resp.endswith("```"):
                text_resp = text_resp[:-3]

            parsed = json.loads(text_resp.strip())
            logger.info(f"Gemini Vision successfully analyzed image: {image_path}")
            return parsed

        except Exception as e:
            logger.warning(f"Failed to analyze image {image_path} with Gemini Vision: {e}. Using fallback OCR.")
            return self._fallback_analysis(image_path, context_caption)

    def _fallback_analysis(self, image_path: str, context_caption: str) -> Dict[str, Any]:
        """Fallback analysis using local Tesseract OCR or basic file info."""
        ocr_text = ""
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            ocr_text = pytesseract.image_to_string(img).strip()
        except Exception:
            ocr_text = ""

        desc = f"Visual element extracted from document page. Caption context: '{context_caption}'."
        if ocr_text:
            desc += f" Extracted text labels: {ocr_text}"

        return {
            "description": desc,
            "diagram_type": "technical_diagram",
            "components": [],
            "connections": [],
            "text_labels": [ocr_text] if ocr_text else []
        }


vision_analyzer = VisionAnalyzer()
