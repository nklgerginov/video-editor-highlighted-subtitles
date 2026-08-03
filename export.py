"""
Video export module.
Handles creating subtitle clips and exporting the final video with subtitles.
Supports Canva-style positioning.
Supports MoviePy v2.0+ imports.
"""

from PyQt6.QtCore import QThread, pyqtSignal


class VideoExporter(QThread):
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    export_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, video_path, subtitle_lines, output_path, subtitle_style=None):
        super().__init__()
        self.video_path = video_path
        self.subtitle_lines = subtitle_lines
        self.output_path = output_path
        self.subtitle_style = subtitle_style or {}
        self._is_running = True
    
    def run(self):
        try:
            self.message.emit("Loading video...")
            self.progress.emit(10)
            
            # FIX: Use direct imports for MoviePy v2.0+
            from moviepy import VideoFileClip
            video = VideoFileClip(self.video_path)
            
            self.message.emit("Generating subtitle clips...")
            self.progress.emit(30)
            
            subtitle_clips = self._create_subtitle_clips(video)
            
            if not self._is_running:
                video.close()
                return
            
            self.message.emit("Compositing video...")
            self.progress.emit(50)
            
            from moviepy import CompositeVideoClip
            final_video = CompositeVideoClip([video] + subtitle_clips)
            
            self.message.emit("Exporting video...")
            self.progress.emit(70)
            
            final_video.write_videofile(
                self.output_path,
                codec='libx264',
                audio_codec='aac',
                fps=video.fps,
                threads=4,
                preset='slow',
                bitrate='8000k',
                audio_bitrate='192k'
            )
            
            self.progress.emit(100)
            self.message.emit("Export complete!")
            self.export_complete.emit(self.output_path)
            
            video.close()
            final_video.close()
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            traceback_str = traceback.format_exc()
            self.error_occurred.emit(error_msg + "
" + traceback_str)
    
    def stop(self):
        self._is_running = False
    
    def _create_subtitle_clips(self, video):
        # FIX: Use direct import for MoviePy v2.0+
        from moviepy import TextClip
        
        subtitle_clips = []
        
        font_family = self.subtitle_style.get('font', 'Arial')
        fontsize = self.subtitle_style.get('fontsize', 40)
        color = self.subtitle_style.get('color', 'white')
        highlight_color = self.subtitle_style.get('highlight_color', 'yellow')
        stroke_color = self.subtitle_style.get('stroke_color', 'black')
        stroke_width = self.subtitle_style.get('stroke_width', 2)
        highlight_scale = self.subtitle_style.get('highlight_scale', 1.2)
        
        position_x = self.subtitle_style.get('position_x', 0.5)
        position_y = self.subtitle_style.get('position_y', 0.85)
        position = (position_x, position_y)
        
        for line in self.subtitle_lines:
            for word in line.words:
                word_clip = TextClip(
                    word.text,
                    fontsize=fontsize,
                    font=font_family,
                    color=color,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width,
                    bg_color='transparent'
                ).set_position(position).set_start(word.start_time).set_duration(word.end_time - word.start_time)
                
                subtitle_clips.append(word_clip)
                
                highlighted_clip = TextClip(
                    word.text,
                    fontsize=int(fontsize * highlight_scale),
                    font=font_family,
                    color=highlight_color,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width,
                    bg_color='transparent'
                ).set_position(position).set_start(word.start_time).set_duration(word.end_time - word.start_time)
                
                subtitle_clips.append(highlighted_clip)
        
        return subtitle_clips