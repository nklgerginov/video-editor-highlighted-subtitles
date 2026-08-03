# Video Editor with Highlighted Subtitles

A modular desktop application that extracts audio from videos, generates word-level synchronized subtitles using Vosk, and renders videos with highlighted subtitles (similar to YouTube Shorts and Instagram Reels).

## Features

- Speech Detection: Offline speech recognition using Vosk
- Video Export: High-quality video export with subtitles
- Customizable Fonts: Choose from available system fonts for subtitles
- Adjustable Highlight Size: Control how much bigger highlighted words appear
- Highest Quality Settings: Optimized for content creators with 8000k bitrate and slow preset
- Real-time Preview: See subtitles with highlighting as the video plays
- Customizable Appearance: Text color, highlight color, font size, and more

## Modular Architecture

This project uses a modular architecture for easier maintenance and debugging:

main.py - Application entry point
models.py - Data models (SubtitleWord, SubtitleLine)
processing.py - Video processing and subtitle generation
export.py - Video export with subtitles
ui/main_window.py - Main application window
ui/preview.py - Subtitle preview widget

## Key Fixes

1. Fixed Highlighting: Only currently active word appears highlighted
2. Fixed Subtitle Generation: Proper line grouping with reset
3. Improved Quality: 8000k bitrate, slow preset

## Requirements

Python 3.8+
PyQt6
moviepy
pydub
SpeechRecognition
vosk
numpy
ffmpeg

## Installation

pip install -r requirements.txt
Download Vosk model: https://alphacephei.com/vosk/models

## Usage

python main.py