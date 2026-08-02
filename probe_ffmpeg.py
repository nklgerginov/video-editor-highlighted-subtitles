import subprocess
import tempfile
from pathlib import Path
from imageio_ffmpeg import get_ffmpeg_exe

ffmpeg = get_ffmpeg_exe()
tmp = Path(tempfile.gettempdir())
video = tmp / "probe_video.mp4"
ass = tmp / "probe_subtitles.ass"
out = tmp / "probe_out.mp4"

if not video.exists():
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=320x240:d=2",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:duration=2",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(video),
        ],
        check=True,
    )

ass.write_text(
    "[Script Info]\n"
    "Title:Probe\n"
    "ScriptType: v4.00+\n"
    "PlayResX:320\n"
    "PlayResY:240\n\n"
    "[V4+ Styles]\n"
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
    "Style: Default,Arial,24,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n\n"
    "[Events]\n"
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    "Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,Hello\n",
    encoding="utf-8",
)

candidates = [
    f"subtitles={str(ass).replace('\\', '/')}",
    f"subtitles='{str(ass).replace('\\', '/')}'",
    f"subtitles=filename='{str(ass).replace('\\', '/')}'",
    f"subtitles='{str(ass).replace('\\', '/').replace(':', '\\:')} '",
    f"subtitles=filename='{str(ass).replace('\\', '/').replace(':', '\\:')} '",
    f"subtitles=filename='{str(ass).replace('\\', '/').replace(':', '\\:')} '",
    f"subtitles='C\\:/Users/vo1d/AppData/Local/Temp/probe_subtitles.ass'",
    f"subtitles=filename='C\\:/Users/vo1d/AppData/Local/Temp/probe_subtitles.ass'",
    f"ass={str(ass).replace('\\', '/').replace(':', '\\:')}",
    f"ass='{str(ass).replace('\\', '/').replace(':', '\\:')} '",
]

for candidate in candidates:
    if out.exists():
        out.unlink()
    print("TRY", candidate)
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video),
        "-vf",
        candidate,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        str(out),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    print("rc", p.returncode)
    stderr = p.stderr or p.stdout or ""
    print(stderr[:2000])
    print("exists", out.exists())
    print("---")
