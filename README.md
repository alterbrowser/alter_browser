# alterbrowser

指纹浏览器 Python 启动 & profile 管理库。将 stealth Chromium 的几十个 `--fingerprint-*` 开关封装成 `Profile` dataclass 和一行启动 API。

---

## 特性

- **一行启动**：`AlterBrowser(seed=12345).launch("https://example.com")`
- **Profile dataclass**：40+ 字段覆盖 UA / GPU / 硬件 / 时区 / 地理 / WebRTC / 字体 / 代理
- **Device Archetype**：按真实设备原型（Dell / ThinkPad / MacBook …）派生一致性指纹
- **IP 自适应**：自动查询出口 IP，对齐 timezone / geolocation / language / 区域字体
- **多模式引擎**：`REALISTIC` / `UNIQUE` / `CUSTOM` 三种指纹策略
- **字体生成器**：`default` / `custom` / `mix` / `system` 四种字体模式
- **CLI**：`python -m alterbrowser launch --seed 12345 https://example.com`
- **零运行时依赖**（仅标准库；socks 代理可选装 `PySocks`）

---

## 致谢 (Credits)

本项目借鉴了以下开源项目的代码：

- [**Ungoogled Chromium**](https://github.com/ungoogled-software/ungoogled-chromium)
- [**fingerprint-chromium**](https://github.com/adryfish/fingerprint-chromium) (by adryfish)

`alterbrowser` 本身只做 **Python 侧的 Profile 管理和 Chrome 命令行组装**，底层 Chromium 二进制请自行基于上述项目构建；本仓库不提供 Chromium 源码或二进制。

各项目均有自己的 License，请分别遵守。

---

## 安装

### 1. 装 Python 库

```bash
pip install alterbrowser
```

### 2. 准备 **patch 过的 Chromium**（必需）

本库需要 patch 过的 stealth Chromium（带 `--fingerprint` 等开关），**不能用普通 Google Chrome**，否则指纹伪装会静默失效。

参考 [致谢章节](#致谢-credits) 中的两个上游项目自行编译，得到 `chrome.exe`。

### 3. 把 `chrome.exe` 放到你脚本旁边（推荐）

```
my-project/
├── run.py              <- 你的脚本
└── chrome.exe          <- patch 过的 Chromium，直接放这
```

然后：

```python
from alterbrowser import AlterBrowser
AlterBrowser().launch("https://example.com")    # 自动找同目录 chrome.exe
```

**其他 chrome 路径方案**（按优先级）：

| 优先级 | 方式 | 适用场景 |
|------|------|---------|
| 1 | 环境变量 `ALTERBROWSER_CHROME_BINARY` | 多脚本共享 |
| 2 | 脚本同目录 `./chrome.exe` | **最推荐** |
| 3 | 脚本子目录 `./chrome/chrome.exe` | 想隔离 |
| 4 | `~/.alterbrowser/chrome/chrome.exe` | 用户级安装 |
| 5 | 构造时显式传 `AlterBrowser(chrome_binary='...')` | 临时覆盖 |

跑 `alterbrowser doctor` 验证装好了：

```bash
alterbrowser doctor
```

---

## 5 分钟上手

**核心思路：任何配置都直接传参数，不需要查 API 手册或记 ID。**

```python
from alterbrowser import AlterBrowser

# 1) 最简 — 什么都不填
AlterBrowser().launch("https://example.com")

# 2) 🔥 直接传你想要的配置（shorthand 自动展开）
AlterBrowser(
    gpu="RTX 5090",        # → gpu_vendor + gpu_renderer
    cpu="i9-14900K",       # → hardware_concurrency + device_memory
    os="win11",            # → platform + platform_version
    resolution="4K",       # → screen_width / height  (也支持 "1920x1080")
    city="Shanghai",       # → timezone + geolocation + language
    proxy="http://user:pass@host:8080",
    fonts_mode="mix",
).launch("https://example.com")

# 3) 想偷懒？用真实机型模板打底（可选）
AlterBrowser(archetype="macbook").launch()              # 模糊匹配
AlterBrowser(archetype="dell", city="NYC").launch()     # archetype 打底 + 自由覆盖
AlterBrowser(archetype="random", gpu="RTX 4090").launch()  # 随机机型 + 覆盖 GPU

# 4) 想可复现？显式传 seed
AlterBrowser(seed=12345, city="Shanghai").launch()

# 5) 持久化
sb.save("profile_001.json")
AlterBrowser.load("profile_001.json").launch()
```

**设计原则**：任何字段都可以直接作为 kwarg 传入 `AlterBrowser(...)`：
- 底层字段：`platform` / `gpu_vendor` / `timezone` / `proxy` / `user_agent` / `extra_args` / ... 总 40+
- Shorthand 便捷字段：`gpu` / `cpu` / `os` / `resolution` / `city`
- 懒人模板：`archetype="<任意关键词>"`（模糊匹配真实机型）

**用户显式给的字段永远优先**，不会被 shorthand 或 archetype 覆盖。

**Shorthand 支持的写法**（大小写和空白不敏感）：

| 字段 | 示例 |
|------|------|
| `gpu` | `"RTX 5090"` / `"RX 7900 XTX"` / `"Arc A770"` / `"UHD 630"` / `"M2 Pro"` / 任意自由字符串 |
| `cpu` | `"i9-14900K"` / `"Ryzen 9 7950X"` / `"M3 Max"` |
| `os` | `"win11"` / `"Windows 10"` / `"macos 14"` / `"Sonoma"` / `"Ubuntu"` |
| `resolution` | `"1920x1080"` / `"4K"` / `"qhd"` / `"1440p"` |
| `city` | `"Shanghai"` / `"NYC"` / `"Tokyo"` / `"Hong Kong"` / `"London"` / 30+ 大城市 |

不在预设表的显卡名会按**品牌关键词**识别（nvidia/radeon/intel/apple），其他字段 fallback 为 no-op。用户显式设置的底层字段始终优先于 shorthand。

**关于 `seed`**：v0.3.1 起完全可选，不传则用"纳秒时间戳 XOR 系统熵"自动生成。seed 只决定 ① `fingerprint_mode=UNIQUE` 下传给 Chrome 的指纹种子 ② 字体混合/variant 选择等确定性派生 ③ `user-data-dir` 默认命名。想可复现时再显式传。

更多场景示例见 [`docs/USAGE.md`](docs/USAGE.md)，所有 API 细节见 [`docs/API.md`](docs/API.md)。

---

## 字体模式速查

| 模式 | 含义 | 使用场景 |
|------|------|----------|
| `default` | 不传 `--fingerprint-fonts`，由上游 seed-hiding 控制 | 多 profile，追求自动化差异 |
| `custom` | 传 `fonts_custom` 作为严格白名单 | 高级用户精确控制 |
| `mix` | 混合风格（Windows + macOS + Linux + Google 混合 70–120 字体） | 标准多账号场景 |
| `system` | 读系统实际安装字体作为白名单 | 最像真实浏览器 |

---

## 项目结构

```
alter_browser/                 ← repo 根
├── alterbrowser/              ← Python 包
│   ├── __init__.py            公开 API 导出
│   ├── __main__.py            CLI 入口
│   ├── browser.py             AlterBrowser 顶层类
│   ├── profile.py             Profile / ProfileBatch dataclass
│   ├── modes.py               FingerprintMode / SourceMode / WebRTCMode / TriState 枚举
│   ├── fonts.py               FontMode / FontGenerator
│   ├── archetype.py           Device Archetype 桥接
│   ├── ip_adapt.py            IP 自适应
│   ├── switches.py            命令行开关构建器
│   ├── launcher.py            subprocess 启动器
│   ├── errors.py              异常类型
│   └── utils.py               seed 派生 / 随机工具
├── tests/                     单元测试 (44 cases)
├── docs/
│   ├── USAGE.md               基础操作指南
│   └── API.md                 完整 API 参考
├── pyproject.toml
├── LICENSE
├── .gitignore
└── README.md
```

---

## CLI 命令

```bash
alterbrowser doctor                          # 诊断环境
alterbrowser archetypes                      # 列出所有机型
alterbrowser cities                          # 列出 city shorthand
alterbrowser launch https://example.com      # 启动（seed 自动生成）
alterbrowser launch --profile my.json
alterbrowser fonts --mode mix                # 生成字体列表
alterbrowser info --profile my.json          # 查看 profile 详情
alterbrowser kill                            # 杀掉所有 chrome
```

---

## 故障排查

### `BinaryNotFoundError: Patched Chromium not found`

跑 `alterbrowser doctor` 看探测路径。最简单的修复：**把 patch 过的 `chrome.exe` 放到你 `.py` 脚本旁边**。

### `doctor` 报 `--help 输出未包含 --fingerprint 开关`

说明这个 chrome 可能是普通 Google Chrome 而非 patch 过的版本。指纹功能会静默失效。换成 patch 版。

### 测试 IP 指纹后仍被检测

1. 跑 `doctor` 确认 patch 能力全部 OK。
2. 检查 `fingerprint_mode`：默认 `REALISTIC`（推荐），如果测试站会做"unique fingerprint"判断，可切 `UNIQUE`。
3. 用 `sb.adapt_to_ip()` 对齐时区 / 地理 / 语言 / 字体，避免交叉校验识破。

### 运行测试

```bash
pytest tests/ -v
```

---

## 版本

见 [CHANGELOG.md](CHANGELOG.md)。当前：**v1.0.0** — API 稳定。

---

## License

MIT — 见 [LICENSE](LICENSE)。
