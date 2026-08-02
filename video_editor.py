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


class SubtitleWord:
    def __init__(self, text, start_time, end_time):
        self.text = text
        self.start_time = start_time
        self.end_time = end_time


class SubtitleLine:
    def __init__(self, words, start_time, end_time):
        self.words = words
        self.start_time = start_time
        self.end_time = end_time
    
    def get_text(self):
        return " ".join(w.text for w in self.words)