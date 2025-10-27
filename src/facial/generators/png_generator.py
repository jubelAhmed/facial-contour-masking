"""
PNG output generator for facial contours.
"""

import base64
from typing import Dict, List

import cv2
import numpy as np

from src.facial.exceptions import ProcessingError
from src.facial.generators.output_generator import OutputGenerator


class PNGGenerator(OutputGenerator):
    """PNG output generator for facial contours."""

    def __init__(self, style: str = "default"):
        """
        Initialize PNG generator with style.

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
        Generate PNG content from landmarks.

        Args:
            landmarks: List of landmark points
            style: Style name

        Returns:
            Base64 encoded PNG content
        """
        try:
            # Create a simple image for testing
            img = np.ones((400, 400, 3), dtype=np.uint8) * 255  # White background

            # Draw some basic shapes based on landmarks
            for i, landmark in enumerate(landmarks):
                x = int(landmark.get("x", 0) * 400)
                y = int(landmark.get("y", 0) * 400)
                cv2.circle(img, (x, y), 2, (0, 0, 255), -1)  # Red dots

            # Add text
            cv2.putText(
                img,
                f"Style: {style}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 0),
                2,
            )
            cv2.putText(
                img,
                f"Landmarks: {len(landmarks)}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 0),
                2,
            )

            # Encode as PNG
            success, buffer = cv2.imencode(".png", img)
            if not success:
                raise ProcessingError("Failed to encode PNG")

            png_data = base64.b64encode(buffer).decode("utf-8")
            return png_data

        except Exception as e:
            raise ProcessingError(f"Failed to generate PNG: {str(e)}")
