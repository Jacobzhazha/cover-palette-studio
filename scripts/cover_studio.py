#!/usr/bin/env python3
"""
Cover Palette Studio (MIT License)
保留 100 套经典配色并重构封面制作方法的一体化零依赖 CLI：
  1. select : 按题材/情绪/用途筛选 Top N 配色，自动计算明暗锁并列出兼容版式
  2. prompt : 引擎 B（纯 AI 一步直出防翻车提示词，带明暗冲突拦截与去土味护栏）或无字主体提示词
  3. render : 引擎 A（精准 HEX 代码排版，零错字、标准像素尺寸，支持 --palettes 多套 1 秒一键换肤）
"""

import argparse
import base64
import html
import json
import mimetypes
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PALETTES_PATH = ROOT / "references" / "palettes-100.json"
LAYOUTS_PATH = ROOT / "references" / "layouts.json"


def load_data():
    with open(PALETTES_PATH, "r", encoding="utf-8") as f:
        p_data = json.load(f)
    with open(LAYOUTS_PATH, "r", encoding="utf-8") as f:
        l_data = json.load(f)
    return p_data["palettes"], l_data["platforms"], l_data["layouts"]


def find_palette(palettes, pid):
    norm = str(pid).strip().lstrip("#").zfill(3)
    for p in palettes:
        if p["number"] == norm or str(p["id"]) == str(pid).strip().lstrip("#"):
            return p
    raise SystemExit(f"[ERROR] 未找到编号为 {pid} 的配色（有效范围 001–100）。")


def find_layout(layouts, lid):
    for ly in layouts:
        if ly["id"] == lid:
            return ly
    valid = ", ".join(x["id"] for x in layouts)
    raise SystemExit(f"[ERROR] 未找到版式 {lid}（可选：{valid}）。")


def compatible_layouts(layouts, bg_tone, engine=None):
    res = []
    for ly in layouts:
        if bg_tone not in ly["allowed_tones"]:
            continue
        if engine and engine not in ly["engines"]:
            continue
        res.append(ly)
    return res


def hex_to_rgb(hx):
    h = hx.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgba(hx, alpha):
    r, g, b = hex_to_rgb(hx)
    return f"rgba({r}, {g}, {b}, {alpha})"


def hex_lum(hx):
    r, g, b = [c / 255.0 for c in hex_to_rgb(hx)]
    lin = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def best_ink_on(bg_hex):
    return "#141519" if hex_lum(bg_hex) >= 0.36 else "#FFFFFF"


def cmd_select(args):
    palettes, _, layouts = load_data()
    q_topics = set(x.strip() for x in (args.topics or "").replace("，", ",").split(",") if x.strip())
    q_moods = set(x.strip() for x in (args.moods or "").replace("，", ",").split(",") if x.strip())
    q_purposes = set(x.strip() for x in (args.purposes or "").replace("，", ",").split(",") if x.strip())

    scored = []
    for p in palettes:
        if args.tone and p["bg_tone"] != args.tone:
            continue
        score = 0.0
        reasons = []
        t_hit = q_topics & set(p["topics"])
        m_hit = q_moods & set(p["moods"])
        u_hit = q_purposes & set(p["purposes"])
        if t_hit:
            score += 20.0 * len(t_hit) / max(1, len(q_topics))
            reasons.append("题材匹配：" + "、".join(sorted(t_hit)))
        if m_hit:
            score += 18.0 * len(m_hit) / max(1, len(q_moods))
            reasons.append("情绪匹配：" + "、".join(sorted(m_hit)))
        if u_hit:
            score += 12.0 * len(u_hit) / max(1, len(q_purposes))
            reasons.append("用途匹配：" + "、".join(sorted(u_hit)))
        # Contrast readability bonus
        if p["roles"]["title_contrast"] >= 7.0:
            score += 4.0
        elif p["roles"]["title_contrast"] >= 4.5:
            score += 2.0
        if not p["roles"]["large_only"]:
            score += 1.5
        scored.append((round(score, 2), p, reasons))

    scored.sort(key=lambda x: (-x[0], x[1]["id"]))
    top = scored[: args.limit]

    out = []
    for sc, p, reasons in top:
        compat_a = [x["id"] for x in compatible_layouts(layouts, p["bg_tone"], "engine-a")]
        compat_b = [x["id"] for x in compatible_layouts(layouts, p["bg_tone"], "engine-b")]
        out.append({
            "number": p["number"],
            "name": p["name"],
            "score": sc,
            "bg_tone": p["bg_tone"],
            "roles": p["roles"],
            "colors": p["colors"],
            "usage": p["usage"],
            "reasons": reasons or ["高对比度通用推荐"],
            "compatible_engine_a_layouts": compat_a,
            "compatible_engine_b_layouts": compat_b,
        })

    print(json.dumps({"recommendations": out}, ensure_ascii=False, indent=2))


def cmd_prompt(args):
    palettes, platforms, layouts = load_data()
    p = find_palette(palettes, args.palette)
    plat = platforms.get(args.platform)
    if not plat:
        raise SystemExit(f"[ERROR] 未知平台 {args.platform}，可选：{', '.join(platforms.keys())}")

    r = p["roles"]
    if args.subject_only:
        subject_desc = args.subject or args.metaphor or args.title or "一台极简笔记本与高效工作流道具"
        accent_list = ", ".join(f"{c['name']}({c['hex']})" for c in p["colors"])
        prompt_text = f"""# 引擎 A · 无字视觉主体生图提示词（搭配配色 #{p['number']} {p['name']}）

Generate ONE 1024x1024 (1:1 aspect ratio) standalone high-craft visual subject illustration for an editorial article cover, with ZERO text, ZERO letters, and ZERO numbers anywhere:

- Subject & Visual Metaphor: {subject_desc}
- Color Harmony Hint: Harmonize key object accents with Palette #{p['number']} {p['name']} ({accent_list}), while avoiding cool gray outer rims so foreground matting stays crisp.
- Visual Style: Soft-matte editorial 3D clay/vinyl toy render or crisp tactile graphic object (Apple / Stripe / Monocle aesthetic), smooth rounded silhouettes, soft even studio lighting, high craft.
- Background (CRITICAL for transparent matting & 1-second palette skin-switching):
  - Completely flat, uniform, solid neutral cool gray background `#b8bec9` from edge to edge.
  - NO floor plane, NO drop shadows cast onto the background, NO outer glow or fog, NO detached floating dots.
  - Keep all elements connected in one compact centered cluster with generous clean `#b8bec9` margin on all four sides.
  - STRICTLY ZERO text, ZERO watermarks, ZERO logos unless explicitly requested.
"""
        print(prompt_text.strip())
        return

    ly = find_layout(layouts, args.layout)
    if "engine-b" not in ly["engines"]:
        choices = ", ".join(x["id"] for x in compatible_layouts(layouts, p["bg_tone"], "engine-b"))
        raise SystemExit(f"[ERROR] 版式 {ly['id']} 不支持整图生图提示词。可选：{choices}")
    if p["bg_tone"] not in ly["allowed_tones"]:
        compat = [f"{x['id']}（{x['name']}）" for x in compatible_layouts(layouts, p["bg_tone"], "engine-b")]
        raise SystemExit(
            f"[明暗冲突拦截] 配色 #{p['number']} {p['name']} 为「{p['bg_tone']}」底色（底色 {r['background']}），"
            f"与版式 {ly['id']}（{ly['name']}，仅支持 {'/'.join(ly['allowed_tones'])} 底色）冲突！\n"
            f"建议改选以下兼容版式之一：{', '.join(compat)}"
        )

    title = (args.title or "把100套配色装进AI").replace("\\n", " / ")
    subtitle = args.subtitle or ""
    metaphor = args.metaphor or "围绕文章核心主题设计单一、清晰、有记忆点的视觉隐喻道具"
    ratio_note = f"目标平台：{plat['label']}，生图比例：{plat['ai_ratio']}（若工具不支持 {plat['ai_ratio']} 则使用 {plat['fallback_ai_ratio']}）"

    prompt_text = f"""# 引擎 B · 防翻车纯 AI 一步直出封面提示词

请创作一张高质量自媒体文章封面图，严格遵循以下配色、版式与去土味护栏：

1. 画幅与构图
- {ratio_note}
- 画面满版出血，不加白色外框、不加卡片圆角边框；为文字留出充足干净的呼吸留白区。

2. 标题文字（简体中文，逐字精准零错字）
- 主标题（最大最醒目，干净扁平排版）：「{title}」
{f'- 副标题（明显弱于主标题，简洁辅助）：「{subtitle}」' if subtitle else '- 副标题：无（保持画面极致干净）'}
- 不额外添加任何虚构刊名、日期、水印、功能图标或密集小字列表。

3. 严格配色分工（#{p['number']} {p['name']} · {p['bg_tone']} 底锁定）
- 主要底色（占 60%–75%）：{r['background']}
- 主标题字色：{r['title']}
- 辅助小字色：{r['body']}
- 少量点缀色（占 5%–15%）：{r['accent']}
- 严禁把所有颜色平均铺满画面，严禁擅自引入杂乱荧光色。

4. 指定版式风格（{ly['name']} / {ly['id']}）
- {ly['ai_style_prompt']}
- 视觉隐喻：{metaphor}

5. 去土味硬护栏（必须遵守）
- 严禁给中文标题加浓重黑描边、硬黑投影或廉价 Word 艺术字立体效果。
- 严禁蓝紫科技渐变、发光全息大脑、悬浮代码雨、毛玻璃圆角弹窗或廉价电商海报感。
- 全图只保留一个主视觉中心与一个清晰隐喻，确保在手机 270px 缩略图下标题一眼清晰可读。
"""
    print(prompt_text.strip())


def encode_image_data_uri(img_path):
    if not img_path:
        return ""
    pth = Path(img_path)
    if not pth.exists():
        raise SystemExit(f"[ERROR] 主体图片不存在：{img_path}")
    mime, _ = mimetypes.guess_type(str(pth))
    mime = mime or "image/png"
    b64 = base64.b64encode(pth.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def build_cover_card_html(p, plat, layout_id, title_lines, subtitle, eyebrow, subject_uri, show_badge):
    w, h = plat["width"], plat["height"]
    ori = plat["layout_orientation"]
    r = p["roles"]
    bg = r["background"]
    title_c = r["title"]
    body_c = r["body"]
    accent = r["accent"]
    is_dark = p["bg_tone"] == "dark"
    grid_line = "rgba(255,255,255,0.08)" if is_dark else "rgba(20,21,25,0.07)"
    subtle_border = "rgba(255,255,255,0.18)" if is_dark else "rgba(20,21,25,0.16)"
    accent_ink = best_ink_on(accent)

    # Extra color strips from palette for crisp geometric accents
    swatches_html = "".join(
        f'<span style="display:inline-block;width:18px;height:18px;background:{c["hex"]};border:1.5px solid {subtle_border}"></span>'
        for c in p["colors"]
    )
    badge_html = (
        f'<div class="palette-badge"><span class="sw-row">{swatches_html}</span>'
        f'<span>#{html.escape(p["number"])} {html.escape(p["name"])} · {html.escape(bg)}</span></div>'
        if show_badge
        else ""
    )

    # Highlight second line if swiss-grid-card
    if layout_id == "swiss-grid-card" and len(title_lines) >= 2:
        t_html = (
            f'<div class="t-line">{html.escape(title_lines[0])}</div>'
            f'<div class="t-line t-highlight"><span>{html.escape(title_lines[1])}</span></div>'
            + "".join(f'<div class="t-line">{html.escape(x)}</div>' for x in title_lines[2:])
        )
    else:
        t_html = "".join(f'<div class="t-line">{html.escape(x)}</div>' for x in title_lines)

    sub_html = f'<div class="subtitle">{html.escape(subtitle)}</div>' if subtitle else ""
    eyebrow_html = f'<div class="eyebrow">{html.escape(eyebrow)}</div>' if eyebrow else ""

    # Layout specific styling & sizing by orientation
    if ori == "landscape":
        pad_x = int(w * 0.055)
        pad_y = int(h * 0.11)
        title_fs = int(min(h * 0.155, 118))
        sub_fs = int(min(h * 0.048, 36))
    elif ori == "portrait":
        pad_x = int(w * 0.075)
        pad_y = int(h * 0.068)
        title_fs = int(min(w * 0.105, 112))
        sub_fs = int(min(w * 0.038, 40))
    else:  # square
        pad_x = int(w * 0.08)
        pad_y = int(h * 0.08)
        title_fs = int(min(w * 0.098, 104))
        sub_fs = int(min(w * 0.036, 38))

    font_stack = (
        '"Songti SC", "Noto Serif CJK SC", "STSong", Georgia, serif'
        if layout_id == "oriental-minimal"
        else '"AlimamaShuHeiTi", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", -apple-system, sans-serif'
    )

    # Pure typographic geometric artwork (zero image-gen needed!)
    if layout_id == "swiss-typo-pure" or not subject_uri:
        extra_c = p["colors"][-1]["hex"] if len(p["colors"]) >= 3 else accent
        deco_html = f"""
        <div class="typo-art">
          <div class="geo-block-1"></div>
          <div class="geo-block-2"></div>
          <div class="geo-num">{html.escape(p["number"])}</div>
        </div>
        """
    else:
        deco_html = f"""
        <div class="hero-stage">
          <div class="hero-glow"></div>
          <img class="hero-img" src="{subject_uri}" alt="cover subject"/>
        </div>
        """

    # Build CSS cleanly per layout + orientation
    grid_bg_css = (
        f"background-image: linear-gradient(to right, {grid_line} 1px, transparent 1px), "
        f"linear-gradient(to bottom, {grid_line} 1px, transparent 1px); background-size: 48px 48px;"
        if layout_id in ("swiss-grid-card", "swiss-typo-pure")
        else f"background-image: radial-gradient(circle at 82% 24%, {rgba(accent, 0.18 if is_dark else 0.14)} 0%, transparent 56%);"
    )

    flex_dir = "row" if ori == "landscape" else "column"
    text_basis = "58%" if ori == "landscape" else "auto"
    media_basis = "42%" if ori == "landscape" else "1"
    stripe_css = (
        f"border-left: 16px solid {accent};" if layout_id == "swiss-grid-card" else ""
    )

    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: {w}px; height: {h}px; overflow: hidden; background: {bg}; }}
  .canvas {{
    position: relative;
    width: {w}px;
    height: {h}px;
    background-color: {bg};
    {grid_bg_css}
    {stripe_css}
    font-family: {font_stack};
    color: {title_c};
    display: flex;
    flex-direction: {flex_dir};
    padding: {pad_y}px {pad_x}px;
    gap: {int(min(w, h) * 0.045)}px;
    overflow: hidden;
  }}
  .text-col {{
    flex: 0 0 {text_basis};
    display: flex;
    flex-direction: column;
    justify-content: center;
    z-index: 2;
    min-width: 0;
  }}
  .eyebrow {{
    display: inline-flex;
    align-self: flex-start;
    align-items: center;
    background: {accent};
    color: {accent_ink};
    font-size: {max(22, int(sub_fs * 0.72))}px;
    font-weight: 800;
    letter-spacing: 1px;
    padding: 8px 18px;
    margin-bottom: {int(title_fs * 0.28)}px;
  }}
  .title-group {{
    display: flex;
    flex-direction: column;
    gap: {int(title_fs * 0.16)}px;
  }}
  .t-line {{
    font-size: {title_fs}px;
    font-weight: 900;
    line-height: 1.12;
    letter-spacing: -0.02em;
    color: {title_c};
    word-break: keep-all;
  }}
  .t-highlight span {{
    display: inline-block;
    background: {accent};
    color: {accent_ink};
    padding: 4px 20px 8px;
    margin-left: -10px;
  }}
  .subtitle {{
    margin-top: {int(title_fs * 0.3)}px;
    font-size: {sub_fs}px;
    font-weight: 700;
    line-height: 1.45;
    color: {body_c};
    opacity: 0.92;
    padding-left: 16px;
    border-left: 5px solid {accent};
  }}
  .palette-badge {{
    position: absolute;
    left: {pad_x}px;
    bottom: {int(pad_y * 0.42)}px;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    font-family: Menlo, Monaco, monospace;
    font-size: {max(18, int(sub_fs * 0.56))}px;
    font-weight: 700;
    color: {body_c};
    opacity: 0.78;
    z-index: 3;
  }}
  .sw-row {{ display: inline-flex; gap: 4px; }}
  .hero-stage {{
    position: relative;
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 0;
    min-height: 0;
    z-index: 2;
  }}
  .hero-glow {{
    position: absolute;
    width: 78%;
    height: 78%;
    border-radius: 50%;
    background: radial-gradient(circle, {rgba(accent, 0.34 if is_dark else 0.22)} 0%, transparent 72%);
    filter: blur(18px);
  }}
  .hero-img {{
    position: relative;
    max-width: 96%;
    max-height: 94%;
    object-fit: contain;
    filter: drop-shadow(0 24px 36px rgba(0, 0, 0, {0.42 if is_dark else 0.18}));
  }}
  .typo-art {{
    position: relative;
    flex: 1;
    min-height: {240 if ori == 'portrait' else 180}px;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1;
  }}
  .geo-block-1 {{
    position: absolute;
    width: {int(min(w, h) * 0.56)}px;
    height: {int(min(w, h) * 0.56)}px;
    background: {accent};
    border-radius: 50%;
    right: {int(w * 0.02)}px;
    bottom: {int(h * 0.04)}px;
    opacity: 0.94;
  }}
  .geo-block-2 {{
    position: absolute;
    width: {int(min(w, h) * 0.34)}px;
    height: {int(min(w, h) * 0.34)}px;
    border: 8px solid {title_c};
    left: {int(w * 0.04)}px;
    top: {int(h * 0.06)}px;
    opacity: 0.85;
  }}
  .geo-num {{
    position: relative;
    font-family: Menlo, Monaco, monospace;
    font-size: {int(min(w, h) * 0.24)}px;
    font-weight: 900;
    color: {accent_ink};
    letter-spacing: -0.05em;
    z-index: 2;
  }}
</style></head><body>
  <div class="canvas" id="cover-canvas">
    <div class="text-col">
      {eyebrow_html}
      <div class="title-group">{t_html}</div>
      {sub_html}
    </div>
    {deco_html}
    {badge_html}
  </div>
</body></html>"""


def cmd_render(args):
    palettes, platforms, layouts = load_data()
    plat = platforms.get(args.platform)
    if not plat:
        raise SystemExit(f"[ERROR] 未知平台 {args.platform}，可选：{', '.join(platforms.keys())}")
    ly = find_layout(layouts, args.layout)
    if "engine-a" not in ly["engines"]:
        compat = [x["id"] for x in layouts if "engine-a" in x["engines"]]
        raise SystemExit(f"[ERROR] 版式 {ly['id']} 仅支持引擎 B（纯 AI 生图），引擎 A 可选：{', '.join(compat)}")

    pids = [x.strip() for x in args.palettes.replace("，", ",").split(",") if x.strip()]
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    title_lines = [line.strip() for line in args.title.replace("\\n", "\n").splitlines() if line.strip()]
    subject_uri = encode_image_data_uri(args.subject) if args.subject else ""

    manifest = []
    preview_cards = []
    for pid in pids:
        p = find_palette(palettes, pid)
        if p["bg_tone"] not in ly["allowed_tones"]:
            print(f"[跳过冲突] #{p['number']} {p['name']} ({p['bg_tone']}) 不适配 {ly['id']}（仅限 {'/'.join(ly['allowed_tones'])}）", file=sys.stderr)
            continue
        card_html = build_cover_card_html(
            p, plat, ly["id"], title_lines, args.subtitle or "", args.eyebrow or "", subject_uri, not args.no_badge
        )
        fname = f"cover-{args.platform}-{ly['id']}-{p['number']}-{p['name']}.html"
        fpath = out_dir / fname
        fpath.write_text(card_html, encoding="utf-8")
        manifest.append({
            "palette": p["number"],
            "name": p["name"],
            "bg_tone": p["bg_tone"],
            "platform": args.platform,
            "layout": ly["id"],
            "width": plat["width"],
            "height": plat["height"],
            "html": str(fpath),
            "png": str(fpath.with_suffix(".png")),
        })
        scale = round(480.0 / plat["width"], 4)
        scaled_h = int(plat["height"] * scale)
        preview_cards.append(f"""
        <div class="preview-item">
          <div class="meta"><strong>#{html.escape(p['number'])} {html.escape(p['name'])}</strong> · {html.escape(p['roles']['background'])} / {html.escape(p['roles']['title'])} / {html.escape(p['roles']['accent'])}</div>
          <div class="frame" style="width:480px;height:{scaled_h}px">
            <iframe src="{html.escape(fname)}" style="width:{plat['width']}px;height:{plat['height']}px;transform:scale({scale});transform-origin:0 0;border:0"></iframe>
          </div>
        </div>""")

    if not manifest:
        raise SystemExit("[ERROR] 所选配色与版式明暗全部冲突，未生成任何封面。")

    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    index_html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>Cover Palette Studio 一键换肤预览</title>
<style>
  body {{ margin:0; padding:28px; background:#f2f3f7; font-family:-apple-system,'PingFang SC',sans-serif; color:#141519; }}
  h1 {{ font-size:22px; margin:0 0 6px; }}
  p {{ margin:0 0 22px; color:#555; font-size:14px; }}
  .grid {{ display:flex; flex-wrap:wrap; gap:24px; }}
  .preview-item {{ background:#fff; padding:14px; border:1px solid #d8dde6; }}
  .meta {{ font-size:13px; margin-bottom:10px; font-family:Menlo,monospace; }}
  .frame {{ overflow:hidden; border:1px solid #141519; }}
</style></head><body>
  <h1>Cover Palette Studio · 一键换肤对照预览（{len(manifest)} 套）</h1>
  <p>平台：{html.escape(plat['label'])}（{plat['width']}×{plat['height']}） · 版式：{html.escape(ly['name'])} · 运行 <code>node scripts/export_png.mjs {html.escape(str(out_dir))}</code> 可批量导出高清 PNG</p>
  <div class="grid">{''.join(preview_cards)}</div>
</body></html>"""
    (out_dir / "index.html").write_text(index_html, encoding="utf-8")
    print(json.dumps({"rendered": len(manifest), "out_dir": str(out_dir), "items": manifest}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Cover Palette Studio — 100套配色一体化自媒体封面工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_sel = sub.add_parser("select", help="按题材/情绪筛选推荐配色与明暗兼容版式")
    p_sel.add_argument("--topics", default="", help="逗号分隔题材，如 科技,效率")
    p_sel.add_argument("--moods", default="", help="逗号分隔情绪，如 冷静,有力")
    p_sel.add_argument("--purposes", default="", help="逗号分隔用途，如 教程,解释")
    p_sel.add_argument("--tone", choices=["light", "dark"], default=None, help="强制限定浅底或深底")
    p_sel.add_argument("--limit", type=int, default=3, help="返回推荐数量")
    p_sel.set_defaults(func=cmd_select)

    p_pr = sub.add_parser("prompt", help="引擎 B：编译防翻车纯 AI 生图提示词（或无字主体提示词）")
    p_pr.add_argument("--palette", required=True, help="配色编号 001–100")
    p_pr.add_argument("--platform", default="wechat", help="wechat / wechat-square / xiaohongshu / video / x")
    p_pr.add_argument("--layout", default="editorial-split", help="版式 ID")
    p_pr.add_argument("--title", default="", help="封面主标题")
    p_pr.add_argument("--subtitle", default="", help="封面副标题")
    p_pr.add_argument("--metaphor", default="", help="画面视觉隐喻说明")
    p_pr.add_argument("--subject-only", action="store_true", help="仅生成用于引擎 A 的无字透明主体提示词")
    p_pr.add_argument("--subject", default="", help="无字主体描述（配合 --subject-only）")
    p_pr.set_defaults(func=cmd_prompt)

    p_ren = sub.add_parser("render", help="引擎 A：精准 HEX 零错字渲染，支持多套配色一键换肤")
    p_ren.add_argument("--platform", default="wechat", help="wechat / wechat-square / xiaohongshu / video / x")
    p_ren.add_argument("--layout", default="editorial-split", help="editorial-split / swiss-grid-card / swiss-typo-pure / oriental-minimal")
    p_ren.add_argument("--palettes", required=True, help="逗号分隔的配色编号，如 073,028,094,065")
    p_ren.add_argument("--title", required=True, help="封面主标题（可用 \\n 换行）")
    p_ren.add_argument("--subtitle", default="", help="副标题")
    p_ren.add_argument("--eyebrow", default="", help="顶部短标签（可选）")
    p_ren.add_argument("--subject", default="", help="本地无字透明 PNG 主体图路径（不传则自动使用几何构图）")
    p_ren.add_argument("--no-badge", action="store_true", help="隐藏左下角配色色号微章")
    p_ren.add_argument("--out", default="./cover-out", help="输出目录")
    p_ren.set_defaults(func=cmd_render)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
