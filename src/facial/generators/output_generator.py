"""
Abstract interface and output format implementations.
"""

import base64
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

# from src.facial.face_schema import MaskContours  # Removed missing import


class OutputGenerator(ABC):
    """Abstract base class for different output formats."""

    @abstractmethod
    def generate(
        self,
        landmarks: List[Dict[str, float]],
        style: str = "default",
    ) -> str:
        pass


class OutputGeneratorFactory:
    """Factory for creating output generators."""

    @staticmethod
    def create_generator(format_type: str) -> OutputGenerator:
        """
        Create generator for specified format.

        Args:
            format_type: Output format (svg, png, json)

        Returns:
            OutputGenerator instance

        Raises:
            ValueError: If format is not supported
        """
        if format_type.lower() == "svg":
            from src.facial.generators.svg_generator import SVGGenerator

            return SVGGenerator()
        elif format_type.lower() == "png":
            from src.facial.generators.png_generator import PNGGenerator

            return PNGGenerator()
        elif format_type.lower() == "json":
            from src.facial.generators.json_generator import JSONGenerator

            return JSONGenerator()
        else:
            raise ValueError(f"Unsupported output format: {format_type}")
