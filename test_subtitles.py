import tempfile
from pathlib import Path
import video_editor


def test_ass_export_uses_simple_filename():
    temp_dir = Path(tempfile.mkdtemp())
    ass_path = temp_dir / "sample_subtitles.ass"
    subtitles = [(0.0, 1.0, "Hello world")]

    window = video_editor.VideoUploaderWindow.__new__(video_editor.VideoUploaderWindow)
    filter_string = window._build_subtitles_filter(ass_path)

    assert filter_string == "subtitles=filename='sample_subtitles.ass'"
    assert ass_path.parent.exists()

    window._write_ass_subtitles(subtitles, ass_path)
    assert ass_path.exists()
    data = ass_path.read_text(encoding="utf-8")
    assert "[Events]" in data
    assert "Dialogue:" in data
