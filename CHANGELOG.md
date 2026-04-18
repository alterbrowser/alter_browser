# Changelog

所有显著变更都记录在这里。格式参考 [Keep a Changelog](https://keepachangelog.com/)。

## [1.0.0] — 2026-04-18

**正式稳定版** — API 不再 breaking change。

### 新增

- **Chrome 路径智能探测**：按 `脚本同目录` → `./chrome/` → 环境变量 → `~/.alterbrowser/chrome/` 顺序搜索。把 patch 过的 `chrome.exe` 丢在 `.py` 旁边就能用。
- **`alterbrowser doctor` CLI**：一键诊断 —— 检查 chrome 是否存在、版本、**patch 能力（--fingerprint 开关是否暴露）**、archetype 库、IP 连通性、dry-run 构建。
- **`alterbrowser archetypes`**：打印可用机型表格（支持 `--region` / `--form-factor` / `--os` 过滤）。
- **`alterbrowser cities`**：打印所有 city shorthand 支持的 32 个城市。
- **`mobile` shorthand**：`AlterBrowser(mobile=True)` 或 `mobile="ios"` 一键切移动端指纹（UA / 屏幕 / 触屏）。
- **`ProfileBatch.launch_all(url, stagger_seconds)`**：批量启动，可配置间隔。
- **`ProfileBatch.summary()`**：友好的批量预览字符串。
- **`print_archetypes()`**：返回 archetype 表格字符串。
- **`py.typed` marker**：IDE / MyPy 现在能识别类型注解。

### 改进

- **故意不探测系统 Google Chrome**：普通 Chrome 不认 `--fingerprint` 等 patch 开关，会导致指纹功能静默失效。库现在只找"patch 过的自编译 Chromium"。
- 屏幕验证下限放宽到 320×400（支持移动端）。
- 报错消息给明确操作指引（中文 + 多种修复方式）。
- CLI `launch --seed` 改为可选。
- Development Status classifier 升级 `Alpha` → `Production/Stable`。

### 修复

- iOS 移动端预设的 `device_memory` 由 6 改为 8（对齐 W3C 枚举）。

---

## [0.3.2] — 2026-04-18

- `AlterBrowser(archetype=...)` 支持短名 / "random" 模糊匹配。
- README 重排示例，突出「直接传参数」主路径。

## [0.3.1] — 2026-04-18

- `seed` 完全可选；不传则用纳秒时间戳 XOR 熵自动生成。

## [0.3.0] — 2026-04-18

- 新增 `gpu` / `cpu` / `os` / `resolution` / `city` shorthand 字段。
- 新增 `alterbrowser.presets` 模块。

## [0.2.1] — 2026-04-18

- 内嵌 `archetype_library`（0.2.0 wheel 遗漏）。

## [0.2.0] — 2026-04-18

首个 PyPI 发布。Device Archetype + IP 自适应 + 多模式引擎 + Shorthand。

## [0.1.0]

MVP。
