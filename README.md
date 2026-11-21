[English](README.en.md)

# Cover Palette Studio · 封面配色工坊

把一个标题做成多套封面，从 **100 套配色、8 种版式**中选择。可用本地 HTML 排版和换色，也可编译一段完整的生图提示词。

[快速开始](#快速开始) · [安装到 Agent](#安装到-agent) · [查看示例](#效果示例) · [下载源码 ZIP](https://github.com/Jacobzhazha/cover-palette-studio/archive/refs/heads/main.zip)

![同一主体应用四种配色的公众号横版封面](examples/wechat-4skins-showcase.png)

| 工作方式 | 用途 | 输出 |
| --- | --- | --- |
| 引擎 A · 本地排版 | 控制文字和色值，用同一份素材批量比较配色 | HTML、预览页，可选 PNG |
| 引擎 B · 整图提示词 | 生成拼贴、像素风和杂志风等图文结合的封面 | 可复制到生图工具的提示词 |

## 快速开始

需要 **Python 3**。选色、编译提示词和生成 HTML 只用 Python 标准库。

```bash
git clone https://github.com/Jacobzhazha/cover-palette-studio.git
cd cover-palette-studio

# 按题材和情绪推荐色号及可用版式
python3 scripts/cover_studio.py select --topics 科技,效率 --moods 冷静,有力 --limit 3

# 生成两张纯文字小红书封面
python3 scripts/cover_studio.py render \
  --platform xiaohongshu --layout swiss-typo-pure --palettes 018,098 \
  --title '下班后用AI\n搭副业工作流' --out cover-out
```

用浏览器打开 `cover-out/index.html` 比较两套配色。需要带插画的封面时，把版式换为 `editorial-split`，用 `--subject ./hero.png` 传入本地图片。透明 PNG 可以直接叠到底色上。

### 导出 PNG

在仓库根目录用 [Playwright](https://playwright.dev/docs/library) 安装 Chromium 并导出。也可以只使用上一步的 HTML。

```bash
npm install --no-save --no-package-lock playwright
npx playwright install chromium
node scripts/export_png.mjs ./cover-out
```

已有 Google Chrome 时，也可使用 `node scripts/export_png.mjs ./cover-out --chrome`，跳过 Chromium 下载。

### 生成整图提示词

```bash
python3 scripts/cover_studio.py prompt \
  --palette 028 --layout retro-torn-collage --platform xiaohongshu \
  --title '下班后用AI搭副业' --subtitle '3个实操清单' \
  --metaphor '复古台灯照亮笔记本与勾选清单'
```

把输出粘贴到豆包、即梦、Gemini 或 ChatGPT 等生图工具。只想生成插画主体时，用 `prompt --palette 073 --subject-only --subject '一台笔记本和一盏台灯'`。

## 平台尺寸

| 平台 | 参数 | HTML／PNG 尺寸 |
| --- | --- | --- |
| 公众号横版 | `wechat` | 1800 × 766 |
| 公众号分享方图 | `wechat-square` | 1080 × 1080 |
| 小红书竖版 | `xiaohongshu` | 1080 × 1440 |
| B站 / YouTube 横版 | `video` | 1920 × 1080 |
| X 文章封面 | `x` | 1500 × 600 |

批量排版自动跳过不匹配的明暗组合，整图提示词会列出兼容版式。[100 套配色](references/palettes-100.json) · [版式定义](references/layouts.json)

## 安装到 Agent

在目标项目下选择对应的路径，确保 `cover-palette-studio/SKILL.md` 与 `scripts/`、`references/` 同层。以 Codex 为例：

```bash
mkdir -p .agents/skills
git clone https://github.com/Jacobzhazha/cover-palette-studio.git .agents/skills/cover-palette-studio
```

| Agent | 项目级安装路径 | 调用 |
| --- | --- | --- |
| Codex | `.agents/skills/cover-palette-studio/` | `$cover-palette-studio` |
| Claude Code | `.claude/skills/cover-palette-studio/` | `/cover-palette-studio` |
| Google Antigravity | `.agents/skills/cover-palette-studio/` | `/cover-palette-studio` |
| OpenCode | `.opencode/skills/cover-palette-studio/` | 在对话里指定 `cover-palette-studio` |

各客户端的安装路径见 [Codex](https://learn.chatgpt.com/docs/build-skills)、[Claude Code](https://code.claude.com/docs/en/skills)、[Antigravity](https://antigravity.google/docs/skills) 和 [OpenCode](https://opencode.ai/docs/skills/)。

## 效果示例

![小红书纯文字封面与插画版式对照](examples/xiaohongshu-showcase.png)
![复古杂志与像素游戏风格的生图示例](examples/engine-b-creative.png)

[MIT 许可证](LICENSE) · 渣渣的赛博宇宙
