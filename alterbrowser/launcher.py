"""
Launcher — 负责真正调用 subprocess.Popen 启动 chrome.exe。

保持无状态，所有配置来自 Profile。
"""
from __future__ import annotations

import logging
import os
import subprocess
from typing import List, Optional

from .errors import BinaryNotFoundError, LaunchTimeoutError
from .profile import Profile
from .switches import build_switches


logger = logging.getLogger("alterbrowser.launcher")


def launch_profile(
    profile: Profile,
    override_url: Optional[str] = None,
    wait: bool = False,
    timeout: Optional[float] = None,
) -> subprocess.Popen:
    """
    启动一个 Profile。

    Args:
        profile: 配置
        override_url: 覆盖 profile.start_url
        wait: True 则阻塞到进程退出
        timeout: wait=True 时的超时（秒）

    Returns:
        subprocess.Popen 实例
    """
    if not os.path.isfile(profile.chrome_binary):
        raise BinaryNotFoundError(
            f"chrome.exe not found: {profile.chrome_binary}"
        )

    cmd = build_switches(profile)

    # 如果传了 override_url，替换掉原 start_url（精确匹配）或追加
    if override_url:
        if profile.start_url and cmd and cmd[-1] == profile.start_url:
            cmd[-1] = override_url
        else:
            cmd.append(override_url)

    # 用户数据目录自动创建
    uddir = profile.auto_user_data_dir()
    os.makedirs(uddir, exist_ok=True)

    logger.info("Launching %r seed=%d args=%d", profile.name or "anon", profile.seed, len(cmd))
    logger.debug("CMD: %s", " ".join(cmd))

    try:
        proc = subprocess.Popen(cmd)
    except FileNotFoundError as e:
        raise BinaryNotFoundError(
            f"chrome.exe not executable: {profile.chrome_binary} ({e})"
        ) from e
    except OSError as e:
        raise BinaryNotFoundError(
            f"failed to launch chrome: {e}"
        ) from e

    if wait:
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise LaunchTimeoutError(
                f"chrome process (PID={proc.pid}) did not exit within {timeout}s"
            )

    return proc


def kill_all_chrome() -> int:
    """
    杀掉所有 chrome 进程（Windows）。
    
    Returns:
        被杀进程数。
    """
    import shutil

    if os.name != "nt":
        # 非 Windows 暂不支持
        return 0

    taskkill = shutil.which("taskkill")
    if not taskkill:
        return 0

    try:
        result = subprocess.run(
            [taskkill, "/F", "/IM", "chrome.exe"],
            capture_output=True, text=True, timeout=10,
        )
        # 解析 "成功: 已终止 PID X" 行
        lines = [l for l in result.stdout.splitlines() if "PID" in l or "pid" in l.lower()]
        return len(lines)
    except Exception as e:
        logger.warning("kill_all_chrome failed: %s", e)
        return 0
