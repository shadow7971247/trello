"""Локальный прогон UI-тестов с сохранением MP4 в media/ (без Selenoid/BrowserStack)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "trello_ui"
MEDIA = ROOT / "media"
PYTHON = UI_DIR / ".venv" / "Scripts" / "python.exe"
FFMPEG_CANDIDATES = (
    Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
    Path("/usr/bin/ffmpeg"),
    Path("/usr/local/bin/ffmpeg"),
)


def _resolve_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    for candidate in FFMPEG_CANDIDATES:
        if candidate.is_file():
            return str(candidate)
    raise FileNotFoundError(
        "ffmpeg не найден. Установите ffmpeg или добавьте его в PATH."
    )


def _clean_frames(frames_dir: Path) -> None:
    frames_dir.mkdir(parents=True, exist_ok=True)
    for png in frames_dir.glob("*.png"):
        png.unlink()


def _run_ui_tests(marker: str, frames_dir: Path) -> int:
    env = os.environ.copy()
    env["UI_VIDEO_FRAMES_DIR"] = str(frames_dir)
    env["HEADLESS"] = "true"
    for key in (
        "SELENOID_URL",
        "SELENOID_LOGIN",
        "SELENOID_PASSWORD",
        "SELENOID_HOST",
        "SELENOID_USER",
        "JENKINS_URL",
    ):
        env.pop(key, None)

    cmd = [
        str(PYTHON),
        "-m",
        "pytest",
        "-m",
        marker,
        "--alluredir",
        str(UI_DIR / "allure-results-video"),
        "-q",
    ]
    print(f"pytest -m {marker!r} (локальный Chrome, headless)")
    result = subprocess.run(cmd, cwd=UI_DIR, env=env, check=False)
    return result.returncode


def _encode_mp4(frames_dir: Path, output: Path, *, fps: int = 2) -> None:
    frames = sorted(frames_dir.glob("frame_*.png"))
    if not frames:
        raise RuntimeError(f"Нет кадров в {frames_dir}")

    ffmpeg = _resolve_ffmpeg()
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%04d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    print(f"ffmpeg -> {output.name} ({len(frames)} frames, {fps} fps)")
    subprocess.run(cmd, check=True)


def capture(marker: str, output_name: str, *, fps: int = 2) -> Path:
    frames_dir = MEDIA / f".ui_video_frames_{marker.replace(' ', '_')}"
    _clean_frames(frames_dir)

    exit_code = _run_ui_tests(marker, frames_dir)
    output = MEDIA / output_name
    _encode_mp4(frames_dir, output, fps=fps)

    if exit_code != 0:
        print(f"Warning: pytest exit code {exit_code}, video saved anyway.")
    print(f"Done: {output}")
    return output


def main() -> int:
    if not PYTHON.is_file():
        print(f"Не найден venv: {PYTHON}", file=sys.stderr)
        return 1

    capture("smoke", "ui_smoke_local.mp4", fps=2)
    capture("ui", "ui_full_local.mp4", fps=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
