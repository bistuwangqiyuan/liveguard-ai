"""
liveguard_algo.fusion.explainer
===============================

事件可解释性输出 — 实现 ``REQ-SEC-008``：每条状态迁移事件可被人类审阅。

提供：

* :func:`explain_event` — 把 :class:`StateTransitionEvent` 转成人类可读的报告。
* :func:`to_cloudevent` — 序列化为 CloudEvents 1.0 JSON（用于消息总线）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .state_machine import SignalFrame, StateTransitionEvent, StreamState


_SIGNAL_LABELS = ("face", "person", "reid", "liveness", "action", "audio")
_SIGNAL_LABELS_CN = ("人脸", "人形", "重识别", "活体", "行为", "声纹")


@dataclass
class ExplanationReport:
    headline: str
    summary: str
    contributions: list[dict[str, float]] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)


def explain_event(ev: StateTransitionEvent, model_versions: dict[str, str] | None = None) -> ExplanationReport:
    """生成对外友好的解释报告（中英混合）。"""
    contribs = _per_signal_contributions(ev.signals, ev.weights_used)
    contributions = [
        {"name": en, "label": cn, "score": round(s, 3), "weight": round(w, 3), "contribution": round(c, 3)}
        for en, cn, s, w, c in zip(
            _SIGNAL_LABELS,
            _SIGNAL_LABELS_CN,
            ev.signals.as_tuple(),
            ev.weights_used,
            contribs,
        )
    ]
    headline = _headline(ev)
    summary = _summary(ev)
    actions = _recommend(ev)

    if model_versions:
        for c in contributions:
            c["model_version"] = model_versions.get(c["name"], "unknown")
    return ExplanationReport(
        headline=headline,
        summary=summary,
        contributions=contributions,
        recommended_actions=actions,
    )


def _per_signal_contributions(signals: SignalFrame, weights: tuple[float, ...]) -> list[float]:
    return [s * w for s, w in zip(signals.as_tuple(), weights)]


def _headline(ev: StateTransitionEvent) -> str:
    table = {
        StreamState.ON_DUTY: "✅ 主播已在岗",
        StreamState.BRIEF_AWAY: "⚠️ 主播短暂离开镜头",
        StreamState.LONG_AWAY: "🟠 主播持续离开 ≥ 60 秒（已升级 P1）",
        StreamState.ALERT_ESCALATED: "🚨 主播离岗超过 3 分钟（P0 紧急告警）",
        StreamState.IDLE: "ℹ️ 直播流空闲",
    }
    return table.get(ev.to_state, str(ev.to_state.value))


def _summary(ev: StateTransitionEvent) -> str:
    parts = [
        f"流 {ev.stream_id} 从状态 {ev.from_state.value} 转到 {ev.to_state.value}",
        f"复合融合得分 = {ev.fusion_score:.3f}",
    ]
    if ev.timer_offline_s > 0:
        parts.append(f"累计离开 {ev.timer_offline_s:.1f}s")
    return "；".join(parts)


def _recommend(ev: StateTransitionEvent) -> list[str]:
    if ev.to_state == StreamState.LONG_AWAY:
        return [
            "立即电话/钉钉提醒主播",
            "检查直播伴侣是否被推送广告或弹窗打断",
            "若 60 秒内仍未恢复，将自动升级到 P0",
        ]
    if ev.to_state == StreamState.ALERT_ESCALATED:
        return [
            "拨打紧急电话（自动）",
            "通知值班 NOC 介入",
            "评估是否切换备播或暂停直播间",
        ]
    if ev.to_state == StreamState.ON_DUTY and ev.from_state in (StreamState.LONG_AWAY, StreamState.ALERT_ESCALATED):
        return ["主播已恢复在岗；归档事件供复盘"]
    return []


def to_cloudevent(
    ev: StateTransitionEvent,
    tenant_id: str,
    host_id: str | None = None,
    platform: str = "unknown",
) -> dict[str, Any]:
    """转换为 CloudEvents 1.0 JSON（标准 envelope）。"""
    return {
        "specversion": "1.0",
        "id": ev.event_id,
        "source": f"lvg://tenant/{tenant_id}/stream/{ev.stream_id}",
        "type": _event_type(ev.from_state, ev.to_state),
        "subject": f"stream/{ev.stream_id}",
        "time": datetime.now(UTC).isoformat(timespec="milliseconds"),
        "datacontenttype": "application/json",
        "data": {
            "tenant_id": tenant_id,
            "stream_id": ev.stream_id,
            "host_id": host_id,
            "platform": platform,
            "severity": ev.severity,
            "state_transition": {"from": ev.from_state.value, "to": ev.to_state.value},
            "duration_offline_s": ev.timer_offline_s,
            "fusion_score": ev.fusion_score,
            "signal_breakdown": {
                k: round(v, 3) for k, v in zip(_SIGNAL_LABELS, ev.signals.as_tuple())
            },
            "weights_used": {
                k: round(v, 3) for k, v in zip(_SIGNAL_LABELS, ev.weights_used)
            },
        },
    }


def _event_type(_from: StreamState, to: StreamState) -> str:
    if to == StreamState.LONG_AWAY:
        return "lvg.alert.host_offline.v1"
    if to == StreamState.ALERT_ESCALATED:
        return "lvg.alert.host_offline_escalated.v1"
    if to == StreamState.ON_DUTY:
        return "lvg.host.online.v1"
    if to == StreamState.BRIEF_AWAY:
        return "lvg.host.offline.v1"
    return "lvg.stream.state_changed.v1"
