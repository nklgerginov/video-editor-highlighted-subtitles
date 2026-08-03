"""Video processing module for subtitle generation using Vosk."""
import os
import json
import tempfile
from typing import List, Tuple
from moviepy import VideoFileClip
from models import Word, SubtitleLine, VideoProject


class SubtitleGenerator:
    def __init__(self, vosk_model_path: str):
        self.vosk_model_path = vosk_model_path
        self._validate_vosk_model()

    def _validate_vosk_model(self):
        if not os.path.exists(self.vosk_model_path):
            raise FileNotFoundError(f"Vosk model not found at: {self.vosk_model_path}")

    def extract_audio(self, video_path: str, output_audio_path: str = None) -> str:
        if output_audio_path is None:
            output_audio_path = tempfile.mktemp(suffix=".wav")
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(output_audio_path, codec="pcm_s16le", fps=16000)
        audio.close()
        video.close()
        return output_audio_path

    def generate_subtitles(self, audio_path: str, video_duration: float = None) -> Tuple[List[SubtitleLine], float]:
        import vosk
        model = vosk.Model(self.vosk_model_path)
        with open(audio_path, "rb") as f:
            audio_data = f.read()
        rec = vosk.KaldiRecognizer(model, 16000.0)
        rec.SetWords(True)
        chunk_size = 4000
        all_words = []
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            if rec.AcceptWaveform(chunk):
                result = json.loads(rec.Result())
                if "result" in result:
                    for word_info in result["result"]:
                        all_words.append(Word(
                            text=word_info["word"],
                            start_time=float(word_info["start"]),
                            end_time=float(word_info["end"])
                        ))
        final_result = json.loads(rec.FinalResult())
        if "result" in final_result:
            for word_info in final_result["result"]:
                all_words.append(Word(
                    text=word_info["word"],
                    start_time=float(word_info["start"]),
                    end_time=float(word_info["end"])
                ))
        if video_duration is None and all_words:
            video_duration = max(w.end_time for w in all_words)
        elif video_duration is None:
            video_duration = 0.0

        subtitle_lines = []
        current_line = SubtitleLine()
        for i, word in enumerate(all_words):
            if i == 0 or (word.start_time - all_words[i-1].end_time) > 2.0:
                if current_line.words:
                    current_line.end_time = all_words[i-1].end_time
                    subtitle_lines.append(current_line)
                current_line = SubtitleLine()
                current_line.start_time = word.start_time
            current_line.add_word(word)

        if current_line.words:
            current_line.end_time = all_words[-1].end_time
            subtitle_lines.append(current_line)

        for line in subtitle_lines:
            if line.end_time > video_duration:
                line.end_time = video_duration

        return subtitle_lines, video_duration

    def process_video(self, video_path: str, vosk_model_path: str) -> VideoProject:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
            audio_path = tmp_audio.name
        try:
            video = VideoFileClip(video_path)
            duration = video.duration
            video.close()
            self.extract_audio(video_path, audio_path)
            subtitle_lines, _ = self.generate_subtitles(audio_path, duration)
            return VideoProject(
                video_path=video_path,
                vosk_model_path=vosk_model_path,
                subtitles=subtitle_lines
            )
        finally:
            if os.path.exists(audio_path):
                os.unlink(audio_path)