"""
liveguard_edge.source
=====================

统一视频源抽象。

* :class:`SyntheticSource` — 合成棋盘+噪声，默认实现，零依赖。
* :class:`CV2Source` — 基于 OpenCV 的 RTMP/RTSP 拉流；缺少 OpenCV 时延迟导入失败。
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator

import numpy as np


@dataclass(slots=True)
class Frame:
    """单帧视频 + 可选 PCM 音频。"""
    image: np.ndarray | None
    pcm: np.ndarray | None
    timestamp_s: float
    dt: float


class VideoSource(ABC):
    @abstractmethod
    def __iter__(self) -> Iterator[Frame]: ...
    @abstractmethod
    def close(self) -> None: ...


class SyntheticSource(VideoSource):
    """确定性合成源 — 用于 CI 与离线 demo。"""

    def __init__(self, *, fps: int = 5, n_frames: int | None = None, seed: int = 0,
                 blank_after: int | None = None, width: int = 320, height: int = 240) -> None:
        self.fps = fps
        self.n_frames = n_frames
        self.seed = seed
        self.blank_after = blank_after
        self.w = width
        self.h = height

    def __iter__(self) -> Iterator[Frame]:
        rng = np.random.default_rng(self.seed)
        dt = 1.0 / self.fps
        ts = time.time()
        idx = 0
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        base = ((xx // 16 + yy // 16) % 2) * 200 + 30
        while True:
            if self.n_frames is not None and idx >= self.n_frames:
                return
            if self.blank_after is not None and idx >= self.blank_after:
                img = np.zeros((self.h, self.w, 3), dtype=np.uint8)
                pcm = np.zeros(1600, dtype=np.float32)
            else:
                noise = rng.integers(0, 60, size=(self.h, self.w), dtype=np.int16)
                plane = np.clip(base + noise, 0, 255).astype(np.uint8)
                img = np.stack([plane, np.flipud(plane), np.fliplr(plane)], axis=2)
                pcm = rng.standard_normal(1600).astype(np.float32) * 0.2
            ts += dt
            yield Frame(image=img, pcm=pcm, timestamp_s=ts, dt=dt)
            idx += 1

    def close(self) -> None:
        return None


class CV2Source(VideoSource):  # pragma: no cover — 需要 opencv 环境
    def __init__(self, url: str, *, fps_cap: int = 5, reconnect_s: int = 3) -> None:
        try:
            import cv2  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "opencv-python-headless not installed; install liveguard-edge[cv]"
            ) from e
        self._cv2 = cv2
        self._url = url
        self._fps_cap = fps_cap
        self._reconnect = reconnect_s
        self._cap = None

    def _open(self) -> None:
        self._cap = self._cv2.VideoCapture(self._url, self._cv2.CAP_FFMPEG)
        if not self._cap.isOpened():
            raise RuntimeError(f"cannot open stream: {self._url}")

    def __iter__(self) -> Iterator[Frame]:
        if self._cap is None:
            self._open()
        assert self._cap is not None
        dt_min = 1.0 / self._fps_cap
        last = 0.0
        while True:
            ok, frame = self._cap.read()
            if not ok:
                self._cap.release()
                time.sleep(self._reconnect)
                self._open()
                continue
            now = time.time()
            if now - last < dt_min:
                continue
            dt = now - last if last else dt_min
            last = now
            yield Frame(image=frame, pcm=None, timestamp_s=now, dt=dt)

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
