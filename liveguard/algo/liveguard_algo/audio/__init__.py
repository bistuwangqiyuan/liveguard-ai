"""音频：VAD + 声纹（speaker verification）。"""
from .vad import VadFrame, VadProcessorMock
from .speaker import SpeakerVerifierMock, SpeakerProfileGallery

__all__ = [
    "SpeakerProfileGallery",
    "SpeakerVerifierMock",
    "VadFrame",
    "VadProcessorMock",
]
