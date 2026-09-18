"""FFmpeg render: ping-pong the AI clip, then merge video, voice, music and captions into a 1080x1920 MP4.

Everything here builds argument lists (no shell strings); ``run`` executes them. The 15-second video is the AI clip
played forward and backward in a loop with a slow camera drift, so its motion repeats; the voice, captions and music
carry the ad.
"""
import json
import subprocess

from advvideo.captions import _ffq

W, H = 1080, 1920
FPS = 30
DURATION = 15.0


def run(cmd, log=None):
    """Run an FFmpeg/ffprobe command, echoing the tail of its output on failure."""
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        tail = "\n".join(proc.stdout.strip().splitlines()[-25:])
        raise RuntimeError("command failed (%s): %s\n%s" % (proc.returncode, " ".join(cmd[:3]), tail))
    if log:
        log(proc.stdout)
    return proc.stdout


def buildconf_and_filters(ffmpeg="ffmpeg"):
    conf = subprocess.run([ffmpeg, "-hide_banner", "-buildconf"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
    filters = subprocess.run([ffmpeg, "-hide_banner", "-filters"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
    return conf, filters


def pingpong_cmd(src, dst, ffmpeg="ffmpeg"):
    """Clip played forward then backward (seamless loop unit)."""
    graph = "[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0[v]"
    return [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-filter_complex", graph, "-map", "[v]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", dst]


def kenburns_cmd(image, dst, seconds=DURATION, ffmpeg="ffmpeg"):
    """Fallback when the AI clip is unavailable: slow push-in on the still photo (no AI motion)."""
    frames = int(seconds * FPS)
    vf = ("scale=1620:2880:force_original_aspect_ratio=increase,crop=1620:2880,"
          "zoompan=z='min(1.0+0.0007*on,1.18)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=%d:s=720x1280:fps=%d,setsar=1" % (frames, FPS))
    return [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", image, "-vf", vf, "-frames:v", str(frames),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", dst]


def video_graph(captions, total):
    """Video filter chain ending in label [v]. ``captions`` is {'mode': 'drawtext'|'ass'|'none', ...}."""
    chain = [
        "[0:v]fps=%d" % FPS,
        "scale=%d:%d:force_original_aspect_ratio=increase:flags=lanczos" % (W + 240, H + 400),
        "crop=%d:%d:x='(iw-%d)/2+45*sin(t/2.6)':y='(ih-%d)/2+38*sin(t/3.3)'" % (W, H, W, H),
        "setsar=1",
    ]
    if captions.get("mode") == "drawtext":
        chain += captions["filters"]
    elif captions.get("mode") == "ass":
        chain.append("ass=filename='%s':fontsdir='%s'" % (_ffq(captions["file"]), _ffq(captions["fontsdir"])))
    chain += ["fade=t=in:st=0:d=0.5", "fade=t=out:st=%.2f:d=0.5" % (total - 0.5), "format=yuv420p[v]"]
    return ",".join(chain)


def audio_graph(total, music_gain=0.7):
    """Voice + music: music fades in/out and ducks under the voice (sidechain compression), then loudness-normalised."""
    fade_out_at = max(total - 2.2, 1.0)
    return ";".join([
        "[1:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,apad=whole_dur=%.2f,atrim=0:%.2f,asplit=2[vo1][vo2]" % (total, total),
        "[2:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,volume=%.2f,afade=t=in:st=0:d=1.2,"
        "afade=t=out:st=%.2f:d=2.2,atrim=0:%.2f[mus]" % (music_gain, fade_out_at, total),
        "[mus][vo2]sidechaincompress=threshold=0.03:ratio=9:attack=15:release=350[duck]",
        "[vo1][duck]amix=inputs=2:duration=first:dropout_transition=0,volume=2,alimiter=limit=0.9,"
        "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a]",
    ])


def final_cmd(video_loop_src, voice_wav, music_wav, out_mp4, captions, total=DURATION, ffmpeg="ffmpeg"):
    """Full render. ``video_loop_src`` is the ping-pong clip (looped) or a full-length fallback clip."""
    graph = video_graph(captions, total) + ";" + audio_graph(total)
    return [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-nostats",
        "-stream_loop", "-1", "-i", video_loop_src,
        "-i", voice_wav,
        "-i", music_wav,
        "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
        "-t", "%.2f" % total, "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out_mp4,
    ]


def probe(path, ffprobe="ffprobe"):
    """Stream facts of a finished file as a dict."""
    out = run([ffprobe, "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,duration:format=duration",
               "-of", "json", path])
    data = json.loads(out)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    return {"width": video and video["width"], "height": video and video["height"], "vcodec": video and video["codec_name"],
            "acodec": audio and audio["codec_name"], "duration": float(data["format"]["duration"])}


def check_output(info, total=DURATION):
    """Problems with the finished file (empty means it meets the spec)."""
    problems = []
    if (info["width"], info["height"]) != (W, H):
        problems.append("size is %sx%s, expected %dx%d" % (info["width"], info["height"], W, H))
    if info["vcodec"] != "h264":
        problems.append("video codec is %s" % info["vcodec"])
    if info["acodec"] != "aac":
        problems.append("audio codec is %s" % info["acodec"])
    if abs(info["duration"] - total) > 0.25:
        problems.append("duration is %.2fs, expected %.1fs" % (info["duration"], total))
    return problems
