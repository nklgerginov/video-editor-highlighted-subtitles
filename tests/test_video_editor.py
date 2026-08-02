import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import video_editor


class VideoEditorTests(unittest.TestCase):
    def setUp(self):
        self.app = video_editor.QApplication.instance() or video_editor.QApplication([])
        self.window = video_editor.VideoUploaderWindow()

    def test_style_preset_applies_expected_values(self):
        self.window.apply_style_preset("Streamer Glow")
        self.assertEqual(self.window.font_family, "Montserrat")
        self.assertEqual(self.window.font_size, 34)
        self.assertEqual(self.window.normal_text_color.name(), "#ffffff")
        self.assertEqual(self.window.highlight_text_color.name(), "#ffcc00")

    def test_reset_style_restores_defaults(self):
        self.window.font_family = "Custom"
        self.window.font_size = 20
        self.window.normal_text_color = video_editor.QColor("black")
        self.window.highlight_text_color = video_editor.QColor("green")
        self.window.reset_style_to_defaults()
        self.assertEqual(self.window.font_family, "Arial")
        self.assertEqual(self.window.font_size, 28)
        self.assertEqual(self.window.normal_text_color.name(), "#ffffff")
        self.assertEqual(self.window.highlight_text_color.name(), "#ffff00")

    def test_srt_is_written_into_exports_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "clip.mp4"
            video_path.write_bytes(b"fake")
            self.window.selected_video_path = str(video_path)
            self.window.export_dir = Path(tmpdir) / "exports"
            self.window.export_dir.mkdir(parents=True, exist_ok=True)

            output_path = self.window._write_srt([(0.0, 1.0, "Hello")])
            output_file = Path(output_path)
            self.assertTrue(output_file.exists())
            self.assertEqual(output_file.parent, self.window.export_dir)
            self.assertIn("Hello", output_file.read_text(encoding="utf-8"))

    def test_subtitle_filter_uses_relative_path(self):
        self.assertEqual(
            self.window._build_subtitles_filter(Path("relative.ass")),
            "subtitles=filename='relative.ass'",
        )


if __name__ == "__main__":
    unittest.main()
