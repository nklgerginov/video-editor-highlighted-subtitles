# Video Editor with Highlighted Subtitles

A modular desktop application that extracts audio from videos, generates word-level synchronized subtitles using Vosk, and renders videos with highlighted subtitles.

## Features
- Speech Detection: Offline speech recognition using Vosk
- Video Export: High-quality video export with subtitles
- Customizable Fonts: Choose from available system fonts
- Adjustable Highlight Size: Control how much bigger highlighted words appear
- Highest Quality Settings: Optimized for content creators
- Real-time Preview
- Customizable Appearance

## Modular Architecture
- main.py: Application entry point
- models.py: Data models (SubtitleWord, SubtitleLine)
- processing.py: Video processing and subtitle generation
- export.py: Video export with subtitles
- ui/main_window.py: Main application window
- ui/preview.py: Subtitle preview widget

## Requirements
- Python 3.8+
- PyQt6
- moviepy
- pydub
- SpeechRecognition
- vosk
- numpy
- ffmpeg

## Installation
pip install -r requirements.txt
Download Vosk models: https://alphacephei.com/vosk/models

## Usage
python main.py