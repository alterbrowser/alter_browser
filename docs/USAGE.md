# 基础操作指南

本文档给出 `alterbrowser` 在各种典型场景下的完整代码示例。

所有 API 细节请查 [`API.md`](API.md)。

---

## 目录

1. [最简启动](#1-最简启动)
2. [自定义硬件指纹](#2-自定义硬件指纹)
3. [代理 + 时区/地理 + 语言](#3-代理--时区地理--语言)
4. [字体白名单](#4-字体白名单)
5. [从 Device Archetype 派生（推荐）](#5-从-device-archetype-派生推荐)
6. [IP 自适应](#6-ip-自适应)
7. [持久化 Profile](#7-持久化-profile)
8. [批量 Profile](#8-批量-profile)
9. [克隆 / Diff](#9-克隆--diff)
10. [只构建命令行](#10-只构建命令行调试用)
11. [错误处理](#11-错误处理)
12. [CLI 用法](#12-cli-用法)
13. [环境变量](#13-环境变量)

---

## 1. 最简启动

```python
from alterbrowser import AlterBrowser

AlterBrowser(seed=12345).launch("https://example.com")
```

等价于手写一串 `--fingerprint-*` 开关调用 `subprocess.Popen`。`seed` 是所有派生的种子。

---

## 1.5 Shorthand 简写字段（v0.3+）

不想查 `gpu_renderer` 的完整 ANGLE 字符串？直接这样：

```python
AlterBrowser(
    seed=12345,
    gpu="RTX 5090",          # 或 "M2 Pro" / "RX 7900 XTX" / "Arc A770" / 任意自由字符串
    cpu="i9-14900K",         # 或 "Ryzen 9 7950X" / "M3 Max"
    os="win11",              # 或 "Windows 10" / "macos 14" / "Sonoma" / "Ubuntu"
    resolution="4K",         # 或 "1920x1080" / "qhd" / "1440p"
    city="Shanghai",         # 或 "NYC" / "Tokyo" / "Hong Kong" / "London"
).launch()
```

会自动展开成底层字段：
- `gpu="RTX 5090"` → `gpu_vendor="Google Inc. (NVIDIA)"`, `gpu_renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 5090 ...)"`, `gpu_mode=CUSTOM`
- `cpu="i9-14900K"` → `hardware_concurrency=32`, `device_memory=32`, `cpu_mode/ram_mode=CUSTOM`
- `os="win11"` → `platform="Win32"`, `platform_version="15.0.0"`
- `resolution="4K"` → `screen_width=3840`, `screen_height=2160`
- `city="Shanghai"` → `timezone="Asia/Shanghai"`, `geolocation=(31.23, 121.47, 100)`, `language="zh-CN"`

**规则**：
- shorthand 只填充"未显式设置"的底层字段（等于 dataclass 默认值视为未设置）
- 用户显式给的底层字段始终优先，例如 `AlterBrowser(os="win11", platform="MacIntel")` 的 `platform` 会保持 `MacIntel`
- 不在预设表的 GPU 名会按品牌关键词（`nvidia/radeon/intel/apple`）识别；CPU/OS/resolution/city 对未知值 fallback 为 no-op

---

## 2. 自定义硬件指纹

```python
from alterbrowser import AlterBrowser, SourceMode

sb = AlterBrowser(
    seed=12345,
    platform="Win32",
    platform_version="10.0.0",

    # 硬件
    cpu_mode=SourceMode.CUSTOM,
    hardware_concurrency=8,
    ram_mode=SourceMode.CUSTOM,
    device_memory=16,

    # 分辨率
    screen_width=1920,
    screen_height=1080,
    screen_color_depth=24,

    # GPU
    gpu_mode=SourceMode.CUSTOM,
    gpu_vendor="Google Inc. (NVIDIA)",
    gpu_renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)",
)
sb.launch()
```

> **重点**：`*_mode` 字段决定"是否真的把 Profile 里的值传给 Chrome"。`REAL` = 用真实本机值、不传；`CUSTOM` = 用 Profile 里手填的值；`BY_IP` = IP 自适应派生。

---

## 3. 代理 + 时区/地理 + 语言

```python
from alterbrowser import AlterBrowser, SourceMode

sb = AlterBrowser(
    seed=12345,
    proxy="http://user:pass@proxy.example.com:8080",

    timezone_mode=SourceMode.CUSTOM,
    timezone="America/New_York",

    geolocation_mode=SourceMode.CUSTOM,
    geolocation=(40.7128, -74.0060, 100),  # lat, lon, accuracy_m

    language="en-US",
    accept_lang="en-US,en;q=0.9",
)
sb.launch()
```

---

## 4. 字体白名单

```python
from alterbrowser import AlterBrowser, FontMode, FontGenerator

# a) 混合风格（推荐多账号场景）
AlterBrowser(seed=42, fonts_mode="mix").launch()

# b) 用户自定义严格白名单
AlterBrowser(
    seed=42,
    fonts_mode=FontMode.CUSTOM,
    fonts_custom=["Arial", "Calibri", "Microsoft YaHei", "SimSun"],
).launch()

# c) 系统实际安装字体（最真实）
AlterBrowser(seed=42, fonts_mode="system").launch()

# d) 独立使用 FontGenerator
fg = FontGenerator(seed=42)
print(fg.mixed_style())               # 70–120 字体
print(fg.preset("win10_minimal"))     # 预制 preset
print(fg.system_real())               # 系统真实字体（仅 Windows）
```

---

## 5. 从 Device Archetype 派生（推荐）

Archetype 预先登记了市面常见设备的"硬件组合"（CPU / GPU / 屏幕 / 字体），保证交叉一致性。

```python
from alterbrowser import AlterBrowser

# 列出所有 archetype
for arch in AlterBrowser.list_archetypes():
    print(arch.id, arch.market_share_weight, arch.gpu_renderer_template)

# 从具体 archetype 派生
sb = AlterBrowser.from_archetype(
    "dell_latitude_e6430_2012",
    seed=12345,
    language="en-US",            # 可覆盖任意 Profile 字段
    proxy="http://...",
)
sb.launch()

# 按条件随机抽
sb = AlterBrowser.random_archetype(
    region="US",
    form_factor="laptop",
    os_family="windows",
    seed=42,
)
```

---

## 6. IP 自适应

查询出口 IP → 自动设置 timezone / geolocation / language / 区域字体，避免检测站通过 IP ↔ 指纹交叉校验识别你。

```python
from alterbrowser import AlterBrowser

sb = AlterBrowser.from_archetype("dell_latitude_e6430_2012", seed=12345)

# 通过本机直连查询
info = sb.adapt_to_ip()

# 通过代理查询（保证和浏览器实际出网 IP 一致）
sb.profile.proxy = "http://user:pass@hk-proxy.example.com:8080"
info = sb.adapt_to_ip()

print(info)   # IPInfo(ip='1.2.3.4', country_code='HK', timezone='Asia/Hong_Kong', ...)

sb.launch("https://example.com")
```

**只调整某几项**：

```python
sb.adapt_to_ip(
    adjust_timezone=True,
    adjust_geolocation=True,
    adjust_language=False,   # 保留原 language
    adjust_fonts=False,      # 不追加区域字体
)
```

**支持的国家码 → 语言 / 字体** 见 `alterbrowser.ip_adapt` 中的 `_COUNTRY_LANG` 和 `_REGION_EXTRA_FONTS`。

---

## 7. 持久化 Profile

```python
from alterbrowser import AlterBrowser

sb = AlterBrowser(seed=12345, name="account_001", platform="Win32")
sb.save("profiles/account_001.json")

# 加载
sb2 = AlterBrowser.load("profiles/account_001.json")
sb2.launch()

# 序列化到 dict / json 字符串
d = sb.to_dict()
j = sb.to_json(indent=2)
```

---

## 8. 批量 Profile

```python
from alterbrowser import AlterBrowser, ProfileBatch

batch = ProfileBatch.from_seeds([100, 200, 300])
for p in batch:
    AlterBrowser.from_profile(p).launch("https://example.com")
```

---

## 9. 克隆 / Diff

```python
sb = AlterBrowser(seed=100, platform="Win32")

# 克隆并覆盖字段
sb_mac = sb.clone(seed=200, platform="MacIntel")

# 查差异
diff = sb.diff(sb_mac)
# {'seed': (100, 200), 'platform': ('Win32', 'MacIntel')}
```

---

## 10. 只构建命令行（调试用）

```python
sb = AlterBrowser(seed=42, fonts_mode="mix")
cmd = sb.build_command("https://example.com")
print(" ".join(cmd))
```

---

## 11. 错误处理

```python
from alterbrowser import (
    AlterBrowser,
    AlterBrowserError,
    BinaryNotFoundError,
    ProfileValidationError,
    LaunchTimeoutError,
    IPAdaptError,
)

try:
    sb = AlterBrowser(seed=-1)       # 负数 seed 非法
except ProfileValidationError as e:
    print(f"config error: {e}")

try:
    sb = AlterBrowser(seed=1, chrome_binary="/not/exist")
    sb.launch()
except BinaryNotFoundError as e:
    print(f"chrome not found: {e}")
```

所有自定义异常都继承自 `AlterBrowserError`。

---

## 12. CLI 用法

```bash
# 启动
python -m alterbrowser launch --seed 12345 https://example.com

# 从 JSON
python -m alterbrowser launch --profile profile.json

# 生成字体（打印到 stdout）
python -m alterbrowser fonts --mode mix --seed 42 --cli

# 只打印命令不启动
python -m alterbrowser launch --seed 1 --dry-run https://example.com

# 查看 profile 详情
python -m alterbrowser info --profile profile.json

# 杀掉所有 chrome（Windows）
python -m alterbrowser kill

# 加 -v 看详细日志
python -m alterbrowser --verbose launch --seed 1 https://example.com
```

---

## 13. 环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| `ALTERBROWSER_CHROME_BINARY` | chrome.exe 绝对路径 | 包目录同级 `build/src/out/Default/chrome.exe` |
| `ALTERBROWSER_PROFILES_DIR` | 自动生成的 user-data-dir 基址 | 包目录同级 `profiles/` |

也可以在代码里显式传 `chrome_binary=` / `user_data_dir=` 直接覆盖。
