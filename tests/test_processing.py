"""Tests for the processing module."""
import os
import tempfile
import unittest
from models import Word, SubtitleLine, VideoProject
from processing import SubtitleGenerator


class TestProcessing(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.vosk_model_path = os.path.join(self.temp_dir, "fake-model")
        os.makedirs(self.vosk_model_path, exist_ok=True)
        
        with open(os.path.join(self.vosk_model_path, "model.conf"), "w") as f:
            f.write("fake model config")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_vosk_model_validation(self):
        gen = SubtitleGenerator(self.vosk_model_path)
        self.assertEqual(gen.vosk_model_path, self.vosk_model_path)

    def test_vosk_model_not_found(self):
        with self.assertRaises(FileNotFoundError):
            SubtitleGenerator("/nonexistent/path")


if __name__ == "__main__":
    unittest.main()
