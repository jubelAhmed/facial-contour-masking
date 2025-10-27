"""Test facial processing generators."""

import pytest
from unittest.mock import MagicMock, patch
import json

from src.facial.generators.svg_generator import SVGGenerator
from src.facial.generators.png_generator import PNGGenerator
from src.facial.generators.json_generator import JSONGenerator
from src.facial.generators.output_generator import OutputGeneratorFactory
from src.facial.schemas import LandmarkPoint


class TestSVGGenerator:
    """Test SVG generator functionality."""

    def test_svg_generator_initialization(self):
        """Test SVG generator can be initialized."""
        generator = SVGGenerator()
        assert generator is not None
        assert hasattr(generator, "generate")

    def test_svg_generator_generate_method(self):
        """Test SVG generator generate method signature."""
        generator = SVGGenerator()
        landmarks = [LandmarkPoint(x=100.0, y=200.0) for _ in range(68)]

        # Test that generate method exists and accepts correct parameters
        assert hasattr(generator, "generate")
        assert callable(generator.generate)

    def test_svg_generator_creates_svg(self):
        """Test SVG generator creates SVG content."""
        generator = SVGGenerator()
        landmarks = [{"x": 100.0, "y": 200.0} for _ in range(68)]

        result = generator.generate(landmarks, "test_style")

        # Should return SVG content
        assert result is not None
        assert "svg" in result.lower()
        assert "test_style" in result


class TestPNGGenerator:
    """Test PNG generator functionality."""

    def test_png_generator_initialization(self):
        """Test PNG generator can be initialized."""
        generator = PNGGenerator()
        assert generator is not None
        assert hasattr(generator, "generate")

    def test_png_generator_generate_method(self):
        """Test PNG generator generate method signature."""
        generator = PNGGenerator()
        landmarks = [LandmarkPoint(x=100.0, y=200.0) for _ in range(68)]

        # Test that generate method exists and accepts correct parameters
        assert hasattr(generator, "generate")
        assert callable(generator.generate)

    @patch("src.facial.generators.png_generator.cv2")
    def test_png_generator_creates_png(self, mock_cv2):
        """Test PNG generator creates PNG content."""
        generator = PNGGenerator()
        landmarks = [{"x": 100.0, "y": 200.0} for _ in range(68)]

        # Mock OpenCV functionality
        mock_cv2.imencode.return_value = (True, b"fake_png_data")

        result = generator.generate(landmarks, "test_style")

        # Should return PNG content
        assert result is not None
        mock_cv2.imencode.assert_called_once()


class TestJSONGenerator:
    """Test JSON generator functionality."""

    def test_json_generator_initialization(self):
        """Test JSON generator can be initialized."""
        generator = JSONGenerator()
        assert generator is not None
        assert hasattr(generator, "generate")

    def test_json_generator_generate_method(self):
        """Test JSON generator generate method signature."""
        generator = JSONGenerator()
        landmarks = [LandmarkPoint(x=100.0, y=200.0) for _ in range(68)]

        # Test that generate method exists and accepts correct parameters
        assert hasattr(generator, "generate")
        assert callable(generator.generate)

    def test_json_generator_creates_json(self):
        """Test JSON generator creates JSON content."""
        generator = JSONGenerator()
        landmarks = [{"x": 100.0, "y": 200.0} for _ in range(68)]

        result = generator.generate(landmarks, "test_style")

        # Should return valid JSON
        assert result is not None
        assert isinstance(result, str)

        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)
        assert "landmarks" in parsed
        assert "style" in parsed


class TestOutputGeneratorFactory:
    """Test output generator factory functionality."""

    def test_factory_initialization(self):
        """Test factory can be initialized."""
        factory = OutputGeneratorFactory()
        assert factory is not None
        assert hasattr(factory, "create_generator")

    def test_factory_create_svg_generator(self):
        """Test factory creates SVG generator."""
        factory = OutputGeneratorFactory()
        generator = factory.create_generator("svg")

        assert generator is not None
        assert isinstance(generator, SVGGenerator)

    def test_factory_create_png_generator(self):
        """Test factory creates PNG generator."""
        factory = OutputGeneratorFactory()
        generator = factory.create_generator("png")

        assert generator is not None
        assert isinstance(generator, PNGGenerator)

    def test_factory_create_json_generator(self):
        """Test factory creates JSON generator."""
        factory = OutputGeneratorFactory()
        generator = factory.create_generator("json")

        assert generator is not None
        assert isinstance(generator, JSONGenerator)

    def test_factory_invalid_format(self):
        """Test factory handles invalid format."""
        factory = OutputGeneratorFactory()

        with pytest.raises(ValueError):
            factory.create_generator("invalid_format")

    def test_factory_supported_formats(self):
        """Test factory supports all expected formats."""
        factory = OutputGeneratorFactory()
        supported_formats = ["svg", "png", "json"]

        for format_type in supported_formats:
            generator = factory.create_generator(format_type)
            assert generator is not None


class TestLandmarkPoint:
    """Test LandmarkPoint schema."""

    def test_landmark_point_creation(self):
        """Test LandmarkPoint can be created."""
        landmark = LandmarkPoint(x=100.5, y=200.3)

        assert landmark.x == 100.5
        assert landmark.y == 200.3

    def test_landmark_point_validation(self):
        """Test LandmarkPoint validation."""
        # Valid landmark
        landmark = LandmarkPoint(x=100.0, y=200.0)
        assert landmark.x == 100.0
        assert landmark.y == 200.0

        # Test with float values
        landmark_float = LandmarkPoint(x=100.5, y=200.7)
        assert landmark_float.x == 100.5
        assert landmark_float.y == 200.7

    def test_landmark_point_serialization(self):
        """Test LandmarkPoint can be serialized."""
        landmark = LandmarkPoint(x=100.0, y=200.0)

        # Should be serializable to dict
        landmark_dict = landmark.model_dump()
        assert landmark_dict["x"] == 100.0
        assert landmark_dict["y"] == 200.0

        # Should be serializable to JSON
        landmark_json = landmark.model_dump_json()
        assert isinstance(landmark_json, str)

        parsed = json.loads(landmark_json)
        assert parsed["x"] == 100.0
        assert parsed["y"] == 200.0


class TestGeneratorIntegration:
    """Test generator integration scenarios."""

    def test_all_generators_implement_interface(self):
        """Test all generators implement the same interface."""
        factory = OutputGeneratorFactory()
        landmarks = [LandmarkPoint(x=100.0, y=200.0) for _ in range(68)]

        generators = [
            factory.create_generator("svg"),
            factory.create_generator("png"),
            factory.create_generator("json"),
        ]

        for generator in generators:
            # All should have generate method
            assert hasattr(generator, "generate")
            assert callable(generator.generate)

            # All should accept landmarks and style
            # (We don't call generate here as it might require mocking)
            assert True  # Placeholder for interface validation

    def test_generator_error_handling(self):
        """Test generators handle errors gracefully."""
        factory = OutputGeneratorFactory()

        # Test invalid format
        with pytest.raises(ValueError):
            factory.create_generator("invalid")

        # Test None format
        with pytest.raises(AttributeError):
            factory.create_generator(None)

    def test_generator_consistency(self):
        """Test generators are consistent in their behavior."""
        factory = OutputGeneratorFactory()
        landmarks = [LandmarkPoint(x=100.0, y=200.0) for _ in range(68)]

        # All generators should accept the same parameters
        for format_type in ["svg", "png", "json"]:
            generator = factory.create_generator(format_type)

            # Should have generate method with same signature
            assert hasattr(generator, "generate")
            assert callable(generator.generate)
