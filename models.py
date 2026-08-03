"""
Data models for the video editor with highlighted subtitles.
"""


class SubtitleWord:
    """Represents a word with timing information for highlighting."""
    def __init__(self, text, start_time, end_time):
        self.text = text
        self.start_time = start_time  # in seconds
        self.end_time = end_time      # in seconds

    def __repr__(self):
        return f"SubtitleWord(text='{self.text}', start={self.start_time:.2f}, end={self.end_time:.2f})"


class SubtitleLine:
    """Represents a line of subtitles with multiple words."""
    def __init__(self, words, start_time, end_time):
        self.words = words  # List of SubtitleWord
        self.start_time = start_time
        self.end_time = end_time
    
    def get_text(self):
        """Return the full text of this subtitle line."""
        return " ".join(w.text for w in self.words)
    
    def __repr__(self):
        return f"SubtitleLine(text='{self.get_text()[:30]}...', start={self.start_time:.2f}, end={self.end_time:.2f})"