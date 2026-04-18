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

    # doctor
    d = sub.add_parser("doctor", help="诊断安装状态和 chrome 连通性")

    # archetypes
    a = sub.add_parser("archetypes", help="列出所有可用 device archetype")
    a.add_argument("--region",      default=None)
    a.add_argument("--form-factor", default=None)
    a.add_argument("--os",          default=None, dest="os_family")

    # cities
    c = sub.add_parser("cities", help="列出 city shorthand 支持的城市")

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
        # seed 可选；不传会自动生成
        kw = {}
        if args.seed is not None: kw["seed"] = args.seed
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


def cmd_doctor(args) -> int:
    """一键诊断：检查 patch 过的 chrome.exe 是否到位。"""
    import os as _os
    import subprocess
    ok = True
    print(f"alterbrowser v{__version__}")
    print(f"Python: {sys.version.split()[0]}  ({sys.platform})")

    sb = AlterBrowser()
    binary = sb.profile.chrome_binary
    print(f"\nchrome_binary: {binary}")

    if not _os.path.isfile(binary):
        print("  [FAIL] 文件不存在\n")
        print("  alterbrowser 需要 **patch 过的 Chromium**（带 --fingerprint 等开关），")
        print("  不能用普通 Google Chrome —— 它不认这些开关，指纹伪装会静默失效。\n")
        print("  最简单的修复：把 patch 过的 chrome.exe 放到你 .py 脚本同目录即可。\n")
        print("  探测过的路径（按优先级）：")
        print("    1. 环境变量 $env:ALTERBROWSER_CHROME_BINARY")
        print(f"    2. 脚本同目录: {_os.path.dirname(binary)}\\chrome.exe")
        print(f"    3. 脚本子目录: {_os.path.dirname(binary)}\\chrome\\chrome.exe")
        print(f"    4. ~/.alterbrowser/chrome/chrome.exe")
        print("\n==> FAIL")
        return 1

    print("  [OK] 文件存在")

    # 版本
    try:
        r = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, timeout=5,
            encoding="utf-8", errors="replace",
        )
        version_line = (r.stdout.strip() or r.stderr.strip())[:200]
        if version_line:
            print(f"  [OK] 版本: {version_line}")
    except Exception as e:
        print(f"  [WARN] --version 调用失败: {e}")

    # Patch 能力检测：dry-run build 看是否会生成 --fingerprint 开关，
    # 并检测 chrome 本身是否暴露该开关
    print("\nPatch 能力检测：")
    try:
        r = subprocess.run(
            [binary, "--help"], capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace",
        )
        help_text = (r.stdout or "") + (r.stderr or "")
        markers = ["--fingerprint", "--fingerprint-platform",
                   "--fingerprint-gpu", "--fingerprint-timezone"]
        found = [m for m in markers if m in help_text]
        if found:
            print(f"  [OK] 检测到 {len(found)}/{len(markers)} 个 patch 开关")
        elif help_text:
            print("  [WARN] --help 输出未包含 --fingerprint 开关")
            print("         如果你确认这个 chrome 是 patch 过的，可以忽略（部分构建不打印所有 flag）；")
            print("         否则很可能是拿错了二进制，指纹功能不会生效。")
    except subprocess.TimeoutExpired:
        print("  [WARN] --help 超时（部分 Chromium 版本挂起，不代表 patch 无效）")
    except Exception as e:
        print(f"  [WARN] --help 调用失败: {e}")

    # 其他组件
    from .archetype import ARCHETYPES_AVAILABLE, ARCHETYPES
    print(f"\nArchetype library: {'OK' if ARCHETYPES_AVAILABLE else 'UNAVAILABLE'} "
          f"({len(ARCHETYPES)} models)")

    print("\nSwitch build (dry-run):")
    try:
        cmd = sb.build_command("https://example.com")
        print(f"  [OK] 生成 {len(cmd)} 个命令行参数")
    except Exception as e:
        ok = False
        print(f"  [FAIL] {e}")

    # 可选：IP adapt
    print("\nIP adapt (optional, needs internet):")
    try:
        from .ip_adapt import detect_ip
        info = detect_ip(timeout=3.0)
        if info:
            print(f"  [OK] IP={info.ip}  country={info.country_code}  tz={info.timezone}")
        else:
            print("  [WARN] 所有端点失败（离线或防火墙）")
    except Exception as e:
        print(f"  [WARN] {e}")

    print("\n==> " + ("ALL OK" if ok else "SOME ISSUES (见上)"))
    return 0 if ok else 1


def cmd_archetypes(args) -> int:
    from .archetype import print_archetypes
    print(print_archetypes(
        region=args.region,
        form_factor=args.form_factor,
        os_family=args.os_family,
    ))
    return 0


def cmd_cities(args) -> int:
    from .presets import CITY_PRESETS
    print(f"{'city':<18}  {'timezone':<22}  {'language':<8}  geolocation")
    print("-" * 80)
    for city, v in sorted(CITY_PRESETS.items()):
        geo = v.get("geolocation", (0, 0, 0))
        print(f"{city:<18}  {v['timezone']:<22}  {v['language']:<8}  ({geo[0]:.2f}, {geo[1]:.2f})")
    print(f"\nUsage: AlterBrowser(city='Shanghai').launch()")
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
        "doctor": cmd_doctor,
        "archetypes": cmd_archetypes,
        "cities": cmd_cities,
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
