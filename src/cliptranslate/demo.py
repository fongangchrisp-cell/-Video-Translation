"""A sample clip with sample captions so the editor can be tried without a model download.

Everything here is **invented demo content**, not the output of the speech model.
"""

from __future__ import annotations

from pathlib import Path

from .core import Caption, VideoInfo
from .media import _run, ffmpeg_executable, probe_video

DEMO_SECONDS = 24


def demo_captions() -> list[Caption]:
    """Fresh copies each call, because the editor mutates captions."""
    return [
        Caption(0.5, 3.5, "Hello everyone, and welcome back to the channel.", "Bonjour à tous, et bienvenue sur la chaîne."),
        Caption(3.5, 7.0, "Today I'm going to show you how I make my videos.", "Aujourd'hui, je vais vous montrer comment je fais mes vidéos."),
        Caption(7.0, 10.5, "First, I write a short script in French.", "D'abord, j'écris un court script en français."),
        Caption(10.5, 14.0, "Then I record it with my phone, in good light.", "Ensuite, je l'enregistre avec mon téléphone, avec une bonne lumière."),
        Caption(14.0, 18.0, "This one line was missed by the machine, so a person has to check it.", "Cette ligne a été ratée par la machine, donc une personne doit la vérifier."),
        Caption(18.0, 22.5, "Thanks for watching, and see you in the next video!", "Merci d'avoir regardé, et à bientôt dans la prochaine vidéo !"),
    ]  # fmt: skip


def create_demo_clip(folder: Path) -> VideoInfo:
    """Render a synthetic 24 s test-pattern video with a tone, using the bundled FFmpeg."""
    path = Path(folder) / "demo_clip.mp4"
    result = _run(
        [
            ffmpeg_executable(),
            "-hide_banner",
            "-nostdin",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size=1280x720:rate=25:duration={DEMO_SECONDS}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=330:duration={DEMO_SECONDS}",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(path),
        ],
        timeout=120,
    )
    if result.returncode != 0 or not path.is_file():
        raise RuntimeError(f"Could not create the demo clip: {result.stderr[-300:]}")
    return probe_video(path)
