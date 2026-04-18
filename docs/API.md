# API 参考

本文档涵盖 `alterbrowser` 所有公开 API。

目录：

- [顶层导入](#顶层导入)
- [AlterBrowser](#alterbrowser)
- [Profile](#profile)
- [ProfileBatch](#profilebatch)
- [枚举 (Enums)](#枚举-enums)
  - [FingerprintMode](#fingerprintmode)
  - [SourceMode](#sourcemode)
  - [WebRTCMode](#webrtcmode)
  - [TriState](#tristate)
  - [FontMode](#fontmode)
- [FontGenerator](#fontgenerator)
- [IP 自适应](#ip-自适应)
- [异常](#异常)
- [工具函数](#工具函数)

---

## 顶层导入

```python
from alterbrowser import (
    AlterBrowser,
    Profile,
    ProfileBatch,
    FontMode,
    FontGenerator,
    FingerprintMode,
    SourceMode,
    WebRTCMode,
    TriState,
    # 异常
    AlterBrowserError,
    BinaryNotFoundError,
    ProfileLoadError,
    ProfileValidationError,
    LaunchTimeoutError,
    IPAdaptError,
    InconsistencyWarning,
)
```

---

## AlterBrowser

顶层 API 类。封装 `Profile` + 启动器。

### 构造

```python
AlterBrowser(**profile_fields)
```

所有关键字参数等价于 `Profile` 字段（见下文）。

### 类方法

| 方法 | 说明 |
|------|------|
| `from_profile(profile: Profile) -> AlterBrowser` | 从已有 Profile 构造 |
| `from_dict(data: dict) -> AlterBrowser` | 从 dict 构造（忽略未知字段） |
| `load(path: str) -> AlterBrowser` | 从 JSON 文件加载 |
| `from_archetype(archetype_id, seed=None, variant_id=None, **overrides)` | 从 Device Archetype 派生 |
| `random_archetype(region=None, form_factor=None, os_family=None, seed=None, ...)` | 按条件随机抽一个 archetype |
| `list_archetypes(region=None, form_factor=None, os_family=None)` | 列出符合条件的 archetype |

### 实例方法

| 方法 | 说明 |
|------|------|
| `launch(url=None, wait=False, timeout=None) -> Popen` | 启动 chrome。`wait=True` 阻塞到退出 |
| `build_command(url=None) -> List[str]` | 只拼命令行不启动（调试用） |
| `adapt_to_ip(proxy=None, timeout=8.0, adjust_timezone=True, adjust_geolocation=True, adjust_language=True, adjust_fonts=True)` | IP 自适应，返回 `IPInfo` 或 `None` |
| `save(path: str)` | 保存到 JSON |
| `to_dict() -> dict` | 序列化 |
| `to_json(indent=2) -> str` | 序列化 JSON 字符串 |
| `clone(**overrides) -> AlterBrowser` | 克隆并覆盖字段 |
| `diff(other) -> dict` | 和另一个 AlterBrowser/Profile 的字段差异 |

### 静态方法

| 方法 | 说明 |
|------|------|
| `kill_all() -> int` | 杀掉所有 chrome 进程，返回数量（Windows） |

### 属性代理

`AlterBrowser` 实现了 `__getattr__`，对 Profile 字段的访问会自动转发：

```python
sb = AlterBrowser(seed=100, platform="Win32")
sb.seed         # 100（来自 sb.profile.seed）
sb.platform     # "Win32"
```

---

## Profile

`@dataclass`，描述一个 chromium 启动配置。所有字段：

### 核心

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `seed` | `int` | `0` | 派生种子（所有噪声源头） |
| `name` | `str` | `""` | 可读标识，用于 user_data_dir 命名 |
| `user_data_dir` | `Optional[str]` | `None` | 显式指定用户数据目录，否则自动派生 |

### Archetype（v0.2）

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `archetype_id` | `Optional[str]` | `None` | 设备原型 ID |
| `archetype_selections` | `Optional[dict]` | `None` | archetype 派生的细节（由 `from_archetype` 填充） |
| `fingerprint_mode` | [`FingerprintMode`](#fingerprintmode) | `REALISTIC` | 指纹策略 |

### 浏览器版本

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `brand` | `str` | `"Chrome"` | UA 品牌 |
| `brand_version` | `str` | `"142"` | UA 主版本 |
| `user_agent` | `Optional[str]` | `None` | 完全自定义 UA（覆盖以上） |

### OS / 语言

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `platform` | `str` | `"Win32"` | `navigator.platform` |
| `platform_version` | `str` | `"10.0.0"` | 系统版本 |
| `language` | `str` | `"zh-CN"` | 首选语言 |
| `accept_lang` | `Optional[str]` | 自动派生 | `Accept-Language` 头 |

### 时区 / 地理位置

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `timezone_mode` | [`SourceMode`](#sourcemode) | `REAL` | 时区来源模式 |
| `timezone` | `Optional[str]` | `None` | IANA 时区如 `America/New_York` |
| `geolocation_mode` | `SourceMode` | `REAL` | 地理位置来源模式 |
| `geolocation` | `Optional[(lat, lon, acc)]` | `None` | WGS84 坐标 + 精度米 |

### 硬件

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `cpu_mode` | `SourceMode` | `REAL` | |
| `hardware_concurrency` | `Optional[int]` | `None` | CPU 逻辑核心数（1–128） |
| `ram_mode` | `SourceMode` | `REAL` | |
| `device_memory` | `Optional[float]` | `None` | `navigator.deviceMemory`，合法值 0.25/0.5/1/2/4/8/16/32/64 |
| `screen_width` | `Optional[int]` | `None` | 屏幕宽（640–7680） |
| `screen_height` | `Optional[int]` | `None` | 屏幕高（480–4320） |
| `screen_color_depth` | `Optional[int]` | `None` | 色深 |
| `max_touch_points` | `Optional[int]` | `None` | 触屏点数 |

### WebGL / WebGPU

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `gpu_mode` | `SourceMode` | `REAL` | |
| `gpu_vendor` | `Optional[str]` | `None` | WebGL unmasked vendor |
| `gpu_renderer` | `Optional[str]` | `None` | WebGL unmasked renderer |
| `webgpu_mode` | `SourceMode` | `REAL` | `DISABLED` → `--fingerprint-webgpu=blank` |

### 噪声 / 媒体

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `noise_canvas` | `bool` | `True` | Canvas 2D noise |
| `noise_webgl_image` | `bool` | `True` | WebGL readPixels noise |
| `noise_audio` | `bool` | `True` | AudioBuffer noise |
| `noise_clientrects` | `bool` | `True` | `getClientRects` 噪声 |
| `media_devices_mode` | `SourceMode` | `REAL` | |
| `media_devices` | `Optional[str]` | `None` | 格式 `"audio_in:video_in:audio_out"` |
| `voices_mode` | `SourceMode` | `REAL` | |
| `voices_preset` | `Optional[str]` | `None` | `"windows"` / `"macos"` / `"linux"` |

### 字体

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `fonts_mode` | [`FontMode`](#fontmode) | `DEFAULT` | |
| `fonts_custom` | `List[str]` | `[]` | CUSTOM 模式的严格白名单；MIX 模式会追加到生成结果 |

### WebRTC

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `webrtc_mode` | [`WebRTCMode`](#webrtcmode) | `REAL` | |
| `webrtc_public_ip` | `Optional[str]` | `None` | REPLACE 模式下假的公网 IP |

### 代理 / Cookie

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `proxy` | `Optional[str]` | `None` | 格式 `"http://user:pass@host:port"` 或 `"socks5://..."` |
| `cookies_file` | `Optional[str]` | `None` | Netscape 格式 cookie 文件 |
| `cookies_json` | `Optional[list]` | `None` | JSON cookie 列表 |

### 隐私 / 高级

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `battery_level` | `Optional[float]` | `None` | 0.0–1.0 |
| `connection` | `Optional[str]` | `None` | `"4g"` / `"wifi"` 等 |
| `do_not_track` | [`TriState`](#tristate) | `DEFAULT` | DNT 头 |
| `port_scan_protection` | `bool` | `True` | 阻止 localhost 端口扫描 |
| `port_scan_allow_list` | `List[int]` | `[]` | 放行端口 |
| `hardware_accel` | `TriState` | `DEFAULT` | 硬件加速 |
| `disable_tls_features` | `bool` | `False` | |

### Chrome

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `chrome_binary` | `str` | `$ALTERBROWSER_CHROME_BINARY` | chrome 可执行文件路径 |
| `extra_args` | `List[str]` | `[]` | 追加的命令行参数 |
| `start_url` | `Optional[str]` | `None` | 启动时打开的 URL |

### 方法

| 方法 | 说明 |
|------|------|
| `validate()` | 字段值校验，非法抛 `ProfileValidationError` |
| `to_dict() -> dict` | 序列化（枚举转字符串） |
| `to_json(indent=2) -> str` | 序列化 JSON |
| `save(path: str)` | 保存到 JSON 文件 |
| `from_dict(data: dict) -> Profile` | 类方法：从 dict 构造（未知字段会警告） |
| `load(path: str) -> Profile` | 类方法：从 JSON 加载 |
| `clone(**overrides) -> Profile` | 克隆 + 覆盖 |
| `diff(other: Profile) -> dict` | 字段差异 |
| `auto_user_data_dir(base=None) -> str` | 计算自动 user-data-dir 路径 |

---

## ProfileBatch

```python
from alterbrowser import ProfileBatch

batch = ProfileBatch.from_seeds([100, 200, 300])
len(batch)            # 3
batch[0].seed         # 100
for p in batch:
    ...
```

| 方法 | 说明 |
|------|------|
| `from_seeds(seeds: List[int], **common_fields) -> ProfileBatch` | 类方法：从 seed 列表批量生成，所有 profile 共享 `common_fields` |
| `__iter__ / __getitem__ / __len__` | 支持常规序列操作 |

---

## 枚举 (Enums)

所有枚举都继承自 `str`，方便 JSON 序列化；都有 `parse()` 类方法，可接字符串或枚举实例。

### FingerprintMode

指纹策略 — 决定是否给 chrome 传 `--fingerprint=<seed>`。

| 值 | 含义 |
|----|------|
| `REALISTIC` = `"realistic"` | 默认：不传 seed，Canvas/Audio 用真实硬件 hash |
| `UNIQUE` = `"unique"` | 传 seed，每 profile 独特 hash（可能被检测站标记） |
| `CACHED` = `"cached"` | v0.4 规划：首启采集真实 hash 持久化 |

### SourceMode

通用"模式切换"，决定字段值的来源。用于 `timezone_mode` / `geolocation_mode` / `cpu_mode` / `ram_mode` / `gpu_mode` / `webgpu_mode` / `media_devices_mode` / `voices_mode`。

| 值 | 含义 |
|----|------|
| `REAL` | 用真实本机值（不传字段） |
| `CUSTOM` | 用 Profile 里手填的值 |
| `BY_IP` | 按 IP 推导（IP 自适应） |
| `DISABLED` | 禁用 / 不报告（仅部分字段支持） |

### WebRTCMode

WebRTC IP 处理策略。

| 值 | 含义 |
|----|------|
| `REAL` | 真实 IP（默认不改） |
| `FORWARD` | 正常转发（走代理） |
| `REPLACE` | 替换为假 IP（需 `webrtc_public_ip`） |
| `DISABLED` | 完全禁用 WebRTC |
| `DISABLED_UDP` | 只禁用非代理 UDP |

### TriState

三态开关，用于 `do_not_track` / `hardware_accel` 等。

| 值 | 含义 |
|----|------|
| `DEFAULT` | 用 Chrome 默认 |
| `ON` | 显式开启 |
| `OFF` | 显式关闭 |

`parse()` 支持 `bool` / `None` / 字符串（`"auto"` / `"true"` / `"false"` / `"1"` / `"0"` 等）自动映射。

### FontMode

字体处理模式。

| 值 | 含义 |
|----|------|
| `DEFAULT` = `"default"` | 不传 `--fingerprint-fonts`，由 C++ seed-hiding 决定 |
| `CUSTOM` = `"custom"` | 用 `fonts_custom` 作为严格白名单 |
| `MIXED` = `"mix"` | 混合风格（Windows + macOS + Linux + Google） |
| `SYSTEM_REAL` = `"system"` | 读系统实际安装字体作为白名单 |

---

## FontGenerator

字体列表生成器。

```python
from alterbrowser import FontGenerator, FontMode

fg = FontGenerator(seed=42)
fg.mixed_style()                     # 混合风格 70–120 字体，seed 相同结果幂等
fg.system_real(include_core=True)    # 系统真实字体（Windows PowerShell）
fg.preset("win10_minimal")           # 预制 preset
fg.preset("win10_home")
fg.preset("win10_office")
fg.preset("win11_creative")
fg.generate(FontMode.MIXED)          # 按 mode 分发
fg.generate(FontMode.CUSTOM, custom=["Arial"])
```

| 方法 | 返回 | 说明 |
|------|------|------|
| `mixed_style()` | `List[str]` | 混合风格，幂等 |
| `system_real(include_core=True)` | `List[str]` | 仅 Windows 可用；非 Windows 返回 `CORE_WINDOWS` |
| `preset(name: str)` | `List[str]` | 预制集，未知 name 抛 `ValueError` |
| `generate(mode, custom=None)` | `Optional[List[str]]` | 按 `FontMode` 分发；`DEFAULT` 返回 `None` |

字体池常量（可直接 import）：

- `CORE_WINDOWS` — 核心 Windows 字体
- `WINDOWS_DECO` — Windows 装饰字体
- `CHINESE_FONTS` — 中文字体池
- `MACOS_FONTS` — macOS 字体池
- `LINUX_NOTO_FONTS` — Linux / Noto 字体池
- `GOOGLE_WEB_FONTS` — Google Web 字体池

---

## IP 自适应

模块 `alterbrowser.ip_adapt`。

```python
from alterbrowser.ip_adapt import detect_ip, apply_to_profile, adapt_profile_to_ip, IPInfo
```

### `detect_ip(proxy=None, timeout=8.0) -> Optional[IPInfo]`

多端点兜底查询：`ipapi.co` → `ipwho.is` → `ip-api.com`。全部失败返回 `None`。

### `IPInfo` (dataclass)

| 字段 | 类型 | 说明 |
|------|------|------|
| `ip` | `str` | 出口 IP |
| `country_code` | `str` | ISO 2 字符国家码 |
| `country_name` | `str` | |
| `region` | `str` | 省/州 |
| `city` | `str` | |
| `timezone` | `str` | IANA 时区 |
| `latitude` | `Optional[float]` | |
| `longitude` | `Optional[float]` | |
| `source` | `str` | 端点来源 |

### `apply_to_profile(profile, ip_info, **flags) -> dict`

把 `IPInfo` 映射到 `profile` 字段。返回 `{"timezone": bool, "geolocation": bool, "language": bool, "fonts_added": int}`。

### `adapt_profile_to_ip(profile, proxy=None, timeout=8.0, **flags) -> Optional[IPInfo]`

`detect_ip` + `apply_to_profile` 一步到位。等价于 `AlterBrowser.adapt_to_ip()`。

查表函数：

- `language_for_country(cc: str) -> Tuple[str, str]` — 返回 `(primary, accept_lang)`
- `extra_fonts_for_country(cc: str) -> List[str]` — 该国家/地区的额外字体

---

## 异常

层级：

```
AlterBrowserError          (基类)
├── BinaryNotFoundError    chrome.exe 找不到或无法启动
├── ProfileLoadError       JSON 加载失败 / 格式错
├── ProfileValidationError 字段值非法（seed 为负、geolocation 越界等）
├── LaunchTimeoutError     launch(wait=True, timeout=...) 超时
└── IPAdaptError           所有 IP 查询端点失败

UserWarning
└── InconsistencyWarning   字段不一致的非致命警告
```

---

## 工具函数

模块 `alterbrowser.utils`。

| 函数 | 说明 |
|------|------|
| `random_seed() -> int` | 生成随机 seed |
| `derive_int(seed, salt, low, high) -> int` | 确定性派生整数 |
| `derive_choice(seed, salt, choices) -> Any` | 确定性派生选择 |
| `derive_rng(seed, salt) -> random.Random` | 确定性派生 `random.Random` 实例 |
| `derive_float(seed, salt, low, high) -> float` | 确定性派生浮点数 |
| `safe_filename(s: str) -> str` | 字符串转安全文件名 |

### 环境变量

| 变量 | 说明 |
|------|------|
| `ALTERBROWSER_CHROME_BINARY` | 覆盖默认 chrome 路径 |
| `ALTERBROWSER_PROFILES_DIR` | 覆盖默认 user-data-dir 基址 |

---

## Archetype

模块 `alterbrowser.archetype`，桥接 `archetype_library`（若可用）。

| 函数 | 说明 |
|------|------|
| `get_archetype(archetype_id) -> DeviceArchetype` | 按 ID 取 |
| `list_archetypes(region=None, form_factor=None, os_family=None)` | 过滤列表，按市场权重降序 |
| `random_archetype(seed=None, **filters) -> DeviceArchetype` | 按权重随机抽 |
| `find_archetype_by_hint(gpu_hint="", os_hint="", form_factor_hint="")` | 模糊匹配（迁移用） |
| `build_profile_from_archetype(archetype_id, seed, variant_id=None, **overrides) -> dict` | 派生 Profile 字段字典 |

### Archetype 可用性

若同级找不到 `archetype_library` 包，`ARCHETYPES_AVAILABLE = False`，此时 `get_archetype` 等函数会抛异常或返回空。
