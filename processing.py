"""
Video processing and subtitle generation module.
Handles audio extraction, conversion, and word-level subtitle generation using Vosk.
"""

import os
import json
import wave
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal


class VideoProcessor(QThread):
    """Thread for processing video and generating subtitles."""
    
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    processing_complete = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, video_path, model_path=None):
        super().__init__()
        self.video_path = video_path
        self.model_path = model_path
        self._is_running = True
    
    def run(self):
        """Main processing thread entry point."""
        try:
            self.message.emit("Extracting audio from video...")
            self.progress.emit(10)
            
            audio_path = self._extract_audio()
            if not self._is_running:
                return
            
            self.message.emit("Converting audio format...")
            self.progress.emit(20)
            
            wav_path = self._convert_to_wav(audio_path)
            if not self._is_running:
                return
            
            self.message.emit("Generating subtitles...")
            self.progress.emit(30)
            
            subtitle_lines = self._generate_subtitles(wav_path)
            if not self._is_running:
                return
            
            self.progress.emit(90)
            self.message.emit("Processing complete!")
            self.progress.emit(100)
            self.processing_complete.emit(subtitle_lines)
            
        except Exception as e:
            import traceback
            self.error_occurred.emit(f"Error: {str(e)}\n{traceback.format_exc()}")
    
    def stop(self):
        self._is_running = False
    
    def _extract_audio(self):
        try:
            from moviepy.editor import VideoFileClip
            video = VideoFileClip(self.video_path)
            audio_path = os.path.join(
                os.path.dirname(self.video_path),
                f"{os.path.splitext(os.path.basename(self.video_path))[0]}_audio.mp3"
            )
            video.audio.write_audiofile(audio_path, codec='mp3', bitrate='192k')
            video.close()
            return audio_path
        except Exception as e:
            output_path = os.path.join(
                os.path.dirname(self.video_path),
                f"{os.path.splitext(os.path.basename(self.video_path))[0]}_audio.mp3"
            )
            cmd = [
                'ffmpeg', '-y', '-i', self.video_path,
                '-vn', '-acodec', 'libmp3lame', '-q:a', '2',
                output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
    
    def _convert_to_wav(self, audio_path):
        try:
            from moviepy.editor import AudioFileClip
            audio = AudioFileClip(audio_path)
            wav_path = os.path.join(
                os.path.dirname(audio_path),
                f"{os.path.splitext(os.path.basename(audio_path))[0]}.wav"
            )
            audio.write_audiofile(wav_path, codec='pcm_s16le', fps=16000)
            audio.close()
            return wav_path
        except Exception:
            wav_path = os.path.join(
                os.path.dirname(audio_path),
                f"{os.path.splitext(os.path.basename(audio_path))[0]}.wav"
            )
            cmd = [
                'ffmpeg', '-y', '-i', audio_path,
                '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000',
                wav_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return wav_path
    
    def _generate_subtitles(self, wav_path):
        if not self.model_path:
            raise ValueError("Vosk model path not provided")
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found at: {self.model_path}")
        
        import vosk
        model = vosk.Model(self.model_path)
        
        wf = wave.open(wav_path, "rb")
        
        if wf.getnchannels() != 1:
            wf.close()
            cmd = [
                'ffmpeg', '-y', '-i', wav_path,
                '-ac', '1', '-ar', str(wf.getframerate()),
                wav_path + '.mono.wav'
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            wav_path = wav_path + '.mono.wav'
            wf = wave.open(wav_path, "rb")
        
        if wf.getsampwidth() != 2:
            raise ValueError("Audio must be 16-bit PCM")
        
        rec = vosk.KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)
        
        from models import SubtitleWord, SubtitleLine
        
        subtitle_lines = []
        current_line_words = []
        current_line_start = 0
        
        while self._is_running:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                
                if "result" in result:
                    for item in result["result"]:
                        word = item.get("word", "")
                        start = item.get("start", 0)
                        end = item.get("end", 0)
                        
                        if word:
                            subtitle_word = SubtitleWord(word, start, end)
                            current_line_words.append(subtitle_word)
                            
                            if (end - current_line_start > 5.0) or (len(current_line_words) >= 10):
                                if current_line_words:
                                    line = SubtitleLine(
                                        current_line_words,
                                        current_line_start,
                                        current_line_words[-1].end_time
                                    )
                                    subtitle_lines.append(line)
                                    current_line_words = []
                                    current_line_start = end
            
            self.progress.emit(30 + int((wf.tell() / wf.getnframes()) * 50))
        
        if current_line_words:
            line = SubtitleLine(
                current_line_words,
                current_line_start,
                current_line_words[-1].end_time
            )
            subtitle_lines.append(line)
            current_line_words = []
        
        final_result = json.loads(rec.FinalResult())
        if "result" in final_result:
            current_line_start = 0
            current_line_words = []
            
            for item in final_result["result"]:
                word = item.get("word", "")
                start = item.get("start", 0)
                end = item.get("end", 0)
                
                if word:
                    subtitle_word = SubtitleWord(word, start, end)
                    current_line_words.append(subtitle_word)
                    
                    if (end - current_line_start > 5.0) or (len(current_line_words) >= 10):
                        if current_line_words:
                            line = SubtitleLine(
                                current_line_words,
                                current_line_start,
                                current_line_words[-1].end_time
                            )
                            subtitle_lines.append(line)
                            current_line_words = []
                            current_line_start = end
            
            if current_line_words:
                line = SubtitleLine(
                    current_line_words,
                    current_line_start,
                    current_line_words[-1].end_time
                )
                subtitle_lines.append(line)
        
        wf.close()
        return subtitle_lines