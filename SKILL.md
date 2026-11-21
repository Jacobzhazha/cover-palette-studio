---
name: cover-palette-studio
description: "用 100 套配色和 8 种版式制作公众号、小红书、B站、YouTube 和 X 封面。支持按主题选色、批量换色排版、导出 PNG，以及生成无字主体或整张封面的生图提示词。"
license: MIT
---

# Cover Palette Studio · 封面配色工坊

从标题、摘要或正文提取目标平台、主标题、可选副标题、题材和情绪。目标平台可选 `wechat`、`wechat-square`、`xiaohongshu`、`video`、`x`。命令中的脚本路径相对于本技能目录。

1. 运行 `python3 scripts/cover_studio.py select --topics 科技,效率 --moods 冷静,有力 --limit 3`。读取推荐配色的编号、字色、底色、对比度以及对应模式可用的版式。用户指定色号时保留原色，按库中的明暗分类选择版式。
2. 按需要选一种流程。
   - **精确排版**：运行 `render`，用 `--title` 指定标题，必要时用 `\n` 分行。用 `--palettes` 一次传入多个色号。纯文字封面选 `swiss-typo-pure`，无需生图。有无字主体时用 `--subject` 传入本地图片，透明 PNG 可以直接叠到底色上。需要生成主体提示词时，运行 `prompt --palette 073 --subject-only --subject "核心道具"`。
   - **整图提示词**：运行 `prompt --palette 028 --layout retro-torn-collage --platform xiaohongshu --title "封面标题" --metaphor "一个清晰的视觉主体"`。需要进一步生成图片时，将提示词交给图片工具，按 [封面视觉规范](references/anti-slop-rules.md) 核对画面与中文标题。
3. 使用输出目录的 `index.html` 比较配色。如果需要 PNG，安装 Playwright 和 Chromium 后运行 `node scripts/export_png.mjs <输出目录>`。预览标题是否换行正确、主体是否完整，并检查缩略图可读性。

全部色卡见 [palettes-100.json](references/palettes-100.json)，平台尺寸和版式见 [layouts.json](references/layouts.json)。按用户要求交付 HTML、PNG 或提示词。
