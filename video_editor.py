"""
Video Editor with Highlighted Subtitles

A desktop application that:
1. Extracts audio from uploaded video files
2. Generates word-level synchronized subtitles
3. Renders videos with highlighted subtitles
4. Allows preview and export

Requirements: Python 3.8+, PyQt6, moviepy, pydub, SpeechRecognition, vosk, numpy
Install: pip install -r requirements.txt
Vosk models: https://alphacephei.com/vosk/models
"""

import sys
import os
import json
import wave
import numpy as np
from pathlib import Path
from datetime import timedelta

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QPushButton, QFileDialog, QProgressBar, QComboBox,
    QGroupBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
from PyQt6.QtGui import QPixmap, QIcon, QFont, QPalette, QColor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from pydub import AudioSegment
import speech_recognition as sr