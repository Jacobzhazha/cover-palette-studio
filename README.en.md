[简体中文](README.md)

# Cover Palette Studio

Design covers from a library of **100 palettes and 8 layouts**. Set the exact text and colors in local HTML, or compile a prompt for generating a complete cover in your image tool.

[Quick start](#quick-start) · [Agent installation](#agent-installation) · [Download source ZIP](https://github.com/Jacobzhazha/cover-palette-studio/archive/refs/heads/main.zip)

![One illustration across four WeChat cover palettes](examples/wechat-4skins-showcase.png)

| Workflow | Use it for | Output |
| --- | --- | --- |
| Engine A · Local layouts | Reuse text and artwork while comparing palettes | HTML cover, comparison page, optional PNG |
| Engine B · Cover prompts | Generate collage, pixel-art, and editorial compositions | Prompt to paste into an image generator |

## Quick start

Use **Python 3**. Palette selection, prompt compilation, and HTML generation use the standard library.

```bash
git clone https://github.com/Jacobzhazha/cover-palette-studio.git
cd cover-palette-studio
python3 scripts/cover_studio.py select --topics 科技,效率 --moods 冷静,有力 --limit 3
python3 scripts/cover_studio.py render \
  --platform xiaohongshu --layout swiss-typo-pure --palettes 018,098 \
  --title 'After-work AI\nA starter workflow' --out cover-out
```

Open `cover-out/index.html` in your browser. To add your own illustration, select `editorial-split` and pass a local file with `--subject ./hero.png`. A transparent PNG lets the cover background show through.

### Export PNG files

From the repository root, install [Playwright](https://playwright.dev/docs/library) and Chromium.

```bash
npm install --no-save --no-package-lock playwright
npx playwright install chromium
node scripts/export_png.mjs ./cover-out
```

If Google Chrome is installed, skip the Chromium download and use `node scripts/export_png.mjs ./cover-out --chrome`.

### Compile a cover prompt

```bash
python3 scripts/cover_studio.py prompt \
  --palette 028 --layout retro-torn-collage --platform xiaohongshu \
  --title '下班后用AI搭副业' --subtitle '3个实操清单' \
  --metaphor 'A vintage lamp lighting a notebook and checklist'
```

Paste the result into your image generator. For a standalone text-free illustration, use `prompt --palette 073 --subject-only --subject 'A laptop and a desk lamp'`.

| Platform | Argument | HTML / PNG dimensions |
| --- | --- | --- |
| WeChat landscape | `wechat` | 1800 × 766 |
| WeChat square | `wechat-square` | 1080 × 1080 |
| Xiaohongshu portrait | `xiaohongshu` | 1080 × 1440 |
| Bilibili / YouTube landscape | `video` | 1920 × 1080 |
| X article cover | `x` | 1500 × 600 |

[Palette library](references/palettes-100.json) · [Layout definitions](references/layouts.json) · [Typography and generated cover examples](examples/)

## Agent installation

Clone the whole folder so that `SKILL.md`, `scripts/`, and `references/` stay together. For Codex, run this from the root of the project where you want to use the skill.

```bash
mkdir -p .agents/skills
git clone https://github.com/Jacobzhazha/cover-palette-studio.git .agents/skills/cover-palette-studio
```

| Agent | Project path | Invoke |
| --- | --- | --- |
| Codex | `.agents/skills/cover-palette-studio/` | `$cover-palette-studio` |
| Claude Code | `.claude/skills/cover-palette-studio/` | `/cover-palette-studio` |
| Google Antigravity | `.agents/skills/cover-palette-studio/` | `/cover-palette-studio` |
| OpenCode | `.opencode/skills/cover-palette-studio/` | Ask for `cover-palette-studio` by name |

See the [Codex](https://learn.chatgpt.com/docs/build-skills), [Claude Code](https://code.claude.com/docs/en/skills), [Antigravity](https://antigravity.google/docs/skills), and [OpenCode](https://opencode.ai/docs/skills/) installation guides.

[MIT License](LICENSE) · ZhaZha Cyber Universe (渣渣的赛博宇宙)
