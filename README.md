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

暂不发 PyPI。两种用法：

```bash
# 方式一：加入 PYTHONPATH
git clone <this-repo> alterbrowser
python -c "import alterbrowser; print(alterbrowser.__version__)"

# 方式二：editable install（需要 Python ≥ 3.9）
pip install -e ./alterbrowser
```

配置 chrome 路径（可选，否则用打包默认值）：

```bash
export ALTERBROWSER_CHROME_BINARY="/path/to/your/patched-chrome"
export ALTERBROWSER_PROFILES_DIR="/path/to/profiles"
```

---

## 5 分钟上手

```python
from alterbrowser import AlterBrowser

# 1) 最简：只给一个 seed
AlterBrowser(seed=12345).launch("https://example.com")

# 2) 指定平台 + 字体模式
sb = AlterBrowser(seed=12345, platform="MacIntel", fonts_mode="mix")
sb.launch()

# 3) 从 Device Archetype 派生（v0.2 推荐）
sb = AlterBrowser.from_archetype("dell_latitude_e6430_2012", seed=12345)
sb.adapt_to_ip()           # 按出口 IP 自动对齐时区/地理/语言/字体
sb.launch("https://example.com")

# 4) 持久化
sb.save("profile_001.json")
AlterBrowser.load("profile_001.json").launch()
```

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

## 运行测试

```bash
pytest tests/ -v
```

---

## 版本

- **v0.2.0** — Archetype + IP 自适应 + 多模式引擎（首个 PyPI 发布）
- **v0.1.0** — MVP（Profile + SwitchBuilder + Launcher + CLI + 测试）

---

## License

MIT — 见 [LICENSE](LICENSE)。
