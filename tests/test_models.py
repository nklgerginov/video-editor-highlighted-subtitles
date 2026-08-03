"""Tests for the data models."""
import unittest
from models import Word, SubtitleLine, SubtitleStyle, SubtitlePosition, VideoProject


class TestModels(unittest.TestCase):
    def test_word_creation(self):
        word = Word(text="hello", start_time=0.5, end_time=1.0)
        self.assertEqual(word.text, "hello")
        self.assertEqual(word.start_time, 0.5)
        self.assertEqual(word.end_time, 1.0)
        self.assertFalse(word.is_highlighted)

    def test_subtitle_line(self):
        line = SubtitleLine()
        word1 = Word(text="hello", start_time=0.0, end_time=0.5)
        word2 = Word(text="world", start_time=0.5, end_time=1.0)
        line.add_word(word1)
        line.add_word(word2)
        
        self.assertEqual(len(line.words), 2)
        self.assertEqual(line.text, "hello world")

    def test_subtitle_style_defaults(self):
        style = SubtitleStyle()
        self.assertEqual(style.font_family, "Arial")
        self.assertEqual(style.font_size, 40)
        self.assertEqual(style.highlight_font_size, 60)
        self.assertEqual(style.text_color, "#FFFFFF")
        self.assertEqual(style.highlight_color, "#FFFF00")

    def test_subtitle_position_defaults(self):
        pos = SubtitlePosition()
        self.assertEqual(pos.x, 50)
        self.assertEqual(pos.y, 50)
        self.assertEqual(pos.width, 800)
        self.assertEqual(pos.height, 200)

    def test_video_project(self):
        project = VideoProject(
            video_path="/path/to/video.mp4",
            vosk_model_path="/path/to/model"
        )
        self.assertEqual(project.video_path, "/path/to/video.mp4")
        self.assertEqual(project.vosk_model_path, "/path/to/model")
        self.assertEqual(len(project.subtitles), 0)

    def test_get_all_words(self):
        project = VideoProject()
        line1 = SubtitleLine()
        line1.add_word(Word(text="hello", start_time=0.0, end_time=0.5))
        line1.add_word(Word(text="world", start_time=0.5, end_time=1.0))
        project.subtitles.append(line1)
        
        words = project.get_all_words()
        self.assertEqual(len(words), 2)
        self.assertEqual(words[0].text, "hello")
        self.assertEqual(words[1].text, "world")

    def test_get_active_word_at_time(self):
        project = VideoProject()
        line1 = SubtitleLine()
        line1.add_word(Word(text="hello", start_time=0.0, end_time=0.5))
        line1.add_word(Word(text="world", start_time=0.5, end_time=1.0))
        project.subtitles.append(line1)
        
        active = project.get_active_word_at_time(0.25)
        self.assertIsNotNone(active)
        self.assertEqual(active.text, "hello")
        
        active = project.get_active_word_at_time(0.75)
        self.assertIsNotNone(active)
        self.assertEqual(active.text, "world")
        
        active = project.get_active_word_at_time(2.0)
        self.assertIsNone(active)


if __name__ == "__main__":
    unittest.main()
