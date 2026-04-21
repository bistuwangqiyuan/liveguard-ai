"""通道抽象 + 7 个实现。"""
from .base import Channel, ChannelResult, NotificationJob
from .dingtalk import DingTalkChannel
from .feishu import FeishuChannel
from .push import AppPushChannel
from .sms import SmsChannel
from .voice import VoiceChannel
from .webhook import WebhookChannel
from .wework import WeWorkChannel

CHANNELS: dict[str, type[Channel]] = {
    "webhook": WebhookChannel,
    "sms": SmsChannel,
    "voice": VoiceChannel,
    "ding": DingTalkChannel,
    "wework": WeWorkChannel,
    "feishu": FeishuChannel,
    "push": AppPushChannel,
}

__all__ = [
    "AppPushChannel",
    "CHANNELS",
    "Channel",
    "ChannelResult",
    "DingTalkChannel",
    "FeishuChannel",
    "NotificationJob",
    "SmsChannel",
    "VoiceChannel",
    "WebhookChannel",
    "WeWorkChannel",
]
