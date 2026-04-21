"""Edge Agent CLI — 供运维/工程现场使用。"""

from __future__ import annotations

import argparse
import asyncio

from .agent import AgentConfig, EdgeAgent
from .source import CV2Source, SyntheticSource
from .uploader import SignalUploader, UploaderConfig


def _build_source(args: argparse.Namespace):
    if args.synthetic or not args.rtmp:
        return SyntheticSource(fps=args.fps, blank_after=args.blank_after)
    return CV2Source(args.rtmp, fps_cap=args.fps)


async def _amain(args: argparse.Namespace) -> None:
    src = _build_source(args)
    uploader = SignalUploader(
        UploaderConfig(
            base_url=args.backend, token=args.token, max_retries=args.retries, max_inflight=args.inflight
        )
    )
    agent = EdgeAgent(
        AgentConfig(
            stream_id=args.stream_id,
            tenant_id=args.tenant,
            host_id=args.host_id,
            agent_id=args.agent_id,
            upload_every_n_frames=args.upload_every,
        ),
        source=src,
        uploader=uploader,
    )
    try:
        await agent.run(max_frames=args.max_frames)
    finally:
        await uploader.aclose()
        src.close()

    m = agent.metrics
    print(
        f"[edge] frames={m.frames_processed}  ok={m.uploads_ok}  "
        f"fail={m.uploads_fail}  last_state={m.last_state}  "
        f"last_score={m.last_fusion_score:.3f}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(prog="liveguard-edge", description="LiveGuard Edge Agent")
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="start agent")
    run.add_argument("--stream-id", required=True)
    run.add_argument("--tenant", default="t_demo")
    run.add_argument("--host-id", default="h_default")
    run.add_argument("--agent-id", default="edge-0")
    run.add_argument("--rtmp", default=None)
    run.add_argument("--synthetic", action="store_true")
    run.add_argument("--backend", default="http://localhost:8080")
    run.add_argument("--token", default="dev-token")
    run.add_argument("--fps", type=int, default=5)
    run.add_argument("--upload-every", type=int, default=1)
    run.add_argument("--retries", type=int, default=3)
    run.add_argument("--inflight", type=int, default=16)
    run.add_argument("--max-frames", type=int, default=None)
    run.add_argument("--blank-after", type=int, default=None)

    args = ap.parse_args()
    asyncio.run(_amain(args))


if __name__ == "__main__":
    main()
