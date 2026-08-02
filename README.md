# Video Editor with Highlighted Subtitles

The goal is to make a desktop application that automatically generates word-level synchronized subtitles for videos, with highlighting effects similar to YouTube Shorts and Instagram Reels.

## Features
- Video Upload: Open any video file (MP4, AVI, MOV, MKV, WEBM)
- Audio Extraction: Automatically extracts audio from your video
- Highlighted Subtitles: Generates word-level synchronized subtitles
- Preview: Watch your video with subtitles in real-time
- Export: Save the final video with burned-in subtitles
- Offline: Works completely offline

## Installation

Install the Python dependencies inside your virtual environment:

pip install PyQt6 moviepy pydub SpeechRecognition vosk numpy

## Usage
1. Download a Vosk model from https://alphacephei.com/vosk/models
2. Extract it into the models folder as:
   - models/vosk-model-en-us-0.22-lgraph
3. Run the app:
   - python video_editor.py
4. In the app:
   - Choose a video
   - Click Preview Video to inspect it
   - Click Process Video to verify the video loads
   - Click Generate Subtitles to extract audio and transcribe it with Vosk
   - Click Export Video to save a version with subtitle overlays

## Notes
- The app uses the bundled ffmpeg/ffprobe setup from imageio-ffmpeg when needed.
- Subtitle generation depends on a local Vosk model being present in the models directory.