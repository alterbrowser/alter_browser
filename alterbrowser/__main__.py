"""
CLI 入口 — python -m alterbrowser <subcommand> ...

用法:
    python -m alterbrowser launch --seed 12345 https://example.com
    python -m alterbrowser launch --profile profile.json
    python -m alterbrowser fonts --mode mix --seed 42
    python -m alterbrowser kill
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import List

from . import AlterBrowser, Profile, FontMode, FontGenerator, AlterBrowserError, __version__


def _parser():
    p = argparse.ArgumentParser(prog="alterbrowser", description="alterbrowser CLI")
    p.add_argument("-v", "--version", action="version", version=f"alterbrowser {__version__}")
    p.add_argument("--verbose", action="store_true", help="print DEBUG logs")

    sub = p.add_subparsers(dest="cmd", required=True)

    # launch
    l = sub.add_parser("launch", help="启动一个 profile")
    l.add_argument("url", nargs="?", default=None, help="起始 URL（可选）")
    l.add_argument("--seed", type=int, default=None)
    l.add_argument("--profile", default=None, help="从 JSON 文件加载 profile")
    l.add_argument("--name", default=None)
    l.add_argument("--platform", default=None)
    l.add_argument("--fonts-mode", default=None, choices=[m.value for m in FontMode])
    l.add_argument("--wait", action="store_true", help="阻塞到进程退出")
    l.add_argument("--dry-run", action="store_true", help="只打印命令，不启动")
    l.add_argument("--chrome-binary", default=None)

    # fonts
    f = sub.add_parser("fonts", help="生成字体列表")
    f.add_argument("--seed", type=int, default=42)
    f.add_argument("--mode", default="mix", choices=["mix", "system", "preset"])
    f.add_argument("--preset", default=None, help="preset 名称（mode=preset 时用）")
    f.add_argument("--cli", action="store_true", help="输出 --fingerprint-fonts=... 格式")
    f.add_argument("--json", action="store_true", help="输出 JSON 数组")

    # build-command
    b = sub.add_parser("build-command", help="只构建命令行，不启动")
    b.add_argument("--profile", required=True)
    b.add_argument("url", nargs="?", default=None)

    # kill
    k = sub.add_parser("kill", help="杀掉所有 chrome 进程")

    # info
    i = sub.add_parser("info", help="打印 profile 详情")
    i.add_argument("--profile", required=True)

    return p


def cmd_launch(args) -> int:
    if args.profile:
        sb = AlterBrowser.load(args.profile)
        overrides = {}
        if args.seed is not None: overrides["seed"] = args.seed
        if args.name: overrides["name"] = args.name
        if args.platform: overrides["platform"] = args.platform
        if args.fonts_mode: overrides["fonts_mode"] = args.fonts_mode
        if args.chrome_binary: overrides["chrome_binary"] = args.chrome_binary
        if overrides:
            sb = sb.clone(**overrides)
    else:
        if args.seed is None:
            print("ERROR: --seed required when not loading from --profile", file=sys.stderr)
            return 2
        kw = {"seed": args.seed}
        if args.name: kw["name"] = args.name
        if args.platform: kw["platform"] = args.platform
        if args.fonts_mode: kw["fonts_mode"] = args.fonts_mode
        if args.chrome_binary: kw["chrome_binary"] = args.chrome_binary
        sb = AlterBrowser(**kw)

    if args.dry_run:
        cmd = sb.build_command(args.url)
        print(" ".join(f'"{c}"' if " " in c else c for c in cmd))
        return 0

    try:
        proc = sb.launch(args.url, wait=args.wait)
    except AlterBrowserError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"Launched PID={proc.pid} seed={sb.seed}")
    return 0


def cmd_fonts(args) -> int:
    fg = FontGenerator(seed=args.seed)
    if args.mode == "mix":
        fonts = fg.mixed_style()
    elif args.mode == "system":
        fonts = fg.system_real()
    elif args.mode == "preset":
        if not args.preset:
            print("ERROR: --preset required when mode=preset", file=sys.stderr)
            return 2
        fonts = fg.preset(args.preset)
    else:
        print(f"ERROR: unknown mode {args.mode!r}", file=sys.stderr)
        return 2

    if args.cli:
        print(f"--fingerprint-fonts={','.join(fonts)}")
    elif args.json:
        print(json.dumps(fonts, ensure_ascii=False, indent=2))
    else:
        for f in fonts:
            print(f)
        print(f"\n(total {len(fonts)} fonts, seed={args.seed}, mode={args.mode})", file=sys.stderr)
    return 0


def cmd_build_command(args) -> int:
    sb = AlterBrowser.load(args.profile)
    cmd = sb.build_command(args.url)
    print(" ".join(f'"{c}"' if " " in c else c for c in cmd))
    return 0


def cmd_kill(args) -> int:
    n = AlterBrowser.kill_all()
    print(f"Killed {n} chrome process(es)")
    return 0


def cmd_info(args) -> int:
    p = Profile.load(args.profile)
    print(p.to_json())
    return 0


def main(argv: List[str] = None) -> int:
    args = _parser().parse_args(argv)

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="[%(levelname)s] %(name)s: %(message)s")

    dispatch = {
        "launch": cmd_launch,
        "fonts": cmd_fonts,
        "build-command": cmd_build_command,
        "kill": cmd_kill,
        "info": cmd_info,
    }
    fn = dispatch.get(args.cmd)
    if not fn:
        print(f"Unknown command: {args.cmd}", file=sys.stderr)
        return 2
    try:
        return fn(args)
    except AlterBrowserError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
