# Video Editor with Highlighted Subtitles

A desktop application that automatically generates word-level synchronized subtitles for videos, with highlighting effects similar to YouTube Shorts and Instagram Reels.

## Features
- Video Upload: Open any video file (MP4, AVI, MOV, MKV, WEBM)
- Audio Extraction: Automatically extracts audio from your video
- Highlighted Subtitles: Generates word-level synchronized subtitles
- Preview: Watch your video with subtitles in real-time
- Export: Save the final video with burned-in subtitles
- Offline: Works completely offline

## Installation

pip install PyQt6 moviepy pydub SpeechRecognition vosk numpy

## Usage
1. Download Vosk model from https://alphacephei.com/vosk/models
2. python video_editor.py