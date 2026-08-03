"""
Main entry point for the Video Editor with Highlighted Subtitles application.

This application allows users to:
1. Extract audio from uploaded video files
2. Generate word-level synchronized subtitles using Vosk
3. Render videos with highlighted subtitles (like YouTube Shorts/Instagram Reels)
4. Preview and export the final video

Features:
- Choosable fonts for subtitles
- Choosable highlight size (bigger word)
- Customizable subtitle appearance
- Real-time preview
- Offline speech recognition with Vosk
- Highest quality settings for content creators

Requirements:
- Python 3.8+
- PyQt6
- moviepy
- pydub
- SpeechRecognition
- vosk
- numpy
- ffmpeg

Install dependencies:
    pip install -r requirements.txt

Download Vosk models from:
    https://alphacephei.com/vosk/models
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import VideoEditorApp


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = VideoEditorApp()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()