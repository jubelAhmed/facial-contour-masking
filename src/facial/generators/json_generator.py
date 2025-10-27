"""
JSON output generator for facial contours.
"""

import json
from typing import Dict, List

from src.facial.exceptions import ProcessingError
from src.facial.generators.output_generator import OutputGenerator


class JSONGenerator(OutputGenerator):
    """JSON output generator for facial contours."""

    def __init__(self, style: str = "default"):
        """
        Initialize JSON generator with style.

        Args:
            style: Style name
        """
        self.style = style

    def generate(
        self,
        landmarks: List[Dict[str, float]],
        style: str = "default",
    ) -> str:
        """
        Generate JSON content from landmarks.

        Args:
            landmarks: List of landmark points
            style: Style name

        Returns:
            JSON content as string
        """
        try:
            # Create JSON structure
            result = {
                "style": style,
                "landmarks": landmarks,
                "landmark_count": len(landmarks),
                "metadata": {"generator": "JSONGenerator", "version": "1.0.0"},
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            raise ProcessingError(f"Failed to generate JSON: {str(e)}")
