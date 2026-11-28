#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""glmgenimg.py — glm-image-generation Codex 插件的本地程序化生图 CLI。

等效替换源 skill（skills/image-generation）对 z-ai-web-dev-sdk
`zai.images.generations.create({prompt, size})` 与 `z-ai image` CLI 的调用。
本地不部署该 SDK，且 Ollama 无法文生图——等效为 **Pillow 程序化合成**
（uv 即用即建临时环境承载，或系统 python3 已装 PIL 时进程内直跑）：

  风格模板：gradient（渐变+几何）、poster（标题海报）、banner（斜纹横幅）、
  avatar（字母头像）、card（卡片）
  尺寸白名单：沿源 skill 7 档（1024x1024 等）；调色板：warm/cool/mono/
  dark/sunset/ocean/forest；--seed 可复现。

  语义级文生图（「一只在花园里玩的猫」）本地链不做：见 SKILL.md 诚实降级
  说明（需扩散模型，建议 ComfyUI/SD WebUI/云端服务）。

用法：
  glmgenimg.py gradient -o bg.png --size 1440x720 --palette sunset
  glmgenimg.py poster -o poster.png --title "产品发布会" --subtitle "2026.11.30"
  glmgenimg.py avatar -o me.png --text "Z" --palette cool
  glmgenimg.py card -o cover.png --title "季度报告" --palette mono --seed 7
  glmgenimg.py banner -o hero.png --title "GLM" --size 1440x720 --print-base64
退出码：0 成功 / 1 用法错误 / 2 后端缺失或生成失败（stderr 报因，不假死）。
"""
import argparse
import base64
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

SIZES = ["1024x1024", "768x1344", "864x1152", "1344x768", "1152x864",
         "1440x720", "720x1440"]  # 沿源 skill 支持尺寸白名单
PALETTES = {
    "warm": ["#F6D365", "#FDA085", "#F5576C"],
    "sunset": ["#0F2027", "#203A43", "#FF6B6B", "#FEE140"],
    "cool": ["#4FACFE", "#00F2FE", "#434343"],
    "ocean": ["#2E3192", "#1BFFFF", "#0F2027"],
    "forest": ["#134E5E", "#71B280", "#093028"],
    "mono": ["#E0E0E0", "#9E9E9E", "#212121"],
    "dark": ["#0F0C29", "#302B63", "#24243E"],
    "purple": ["#8E2DE2", "#4A00E0", "#0F0C29"],
}
TIMEOUT = int(os.environ.get("GLM_GENIMG_TIMEOUT", "300"))

WORKER = r'''
import json, math, random, sys
_a = sys.argv[1:]
if _a and _a[0] == "--": _a = _a[1:]
spec = json.load(open(_a[0]))
from PIL import Image, ImageDraw, ImageFilter, ImageFont

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def hx(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))

def fonts(size):
    for fp in ("/System/Library/Fonts/PingFang.ttc",
               "/System/Library/Fonts/Hiragino Sans GB.ttc",
               "/System/Library/Fonts/Supplemental/Songti.ttc",
               "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
               "/System/Library/Fonts/Helvetica.ttc",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None

def gradient_bg(w, h, colors):
    img = Image.new("RGB", (w, h))
    px = img.load()
    stops = [hx(c) for c in colors]
    seg = len(stops) - 1
    for y in range(h):
        t = y / max(1, h - 1) * seg
        i = min(int(t), seg - 1)
        c = lerp(stops[i], stops[i + 1], t - i)
        for x in range(w):
            px[x, y] = c
    return img

def noise_dots(img, rnd, n=140, alpha=40):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for _ in range(n):
        x, y = rnd.randint(0, img.width - 1), rnd.randint(0, img.height - 1)
        r = rnd.randint(1, 4)
        col = (255, 255, 255, rnd.randint(10, alpha))
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    return Image.alpha_composite(img.convert("RGBA"), ov)

def fit_font(text, max_w, start, font_fn):
    size = start
    f = fonts(size)
    while size > 14:
        f = fonts(size)
        if f is None:
            return None, size
        try:
            bb = f.getbbox(text)
            if bb[2] - bb[0] <= max_w:
                return f, size
        except Exception:
            return f, size
        size -= 6
    return f, max(14, size)

try:
    s = spec
    w, h = s["w"], s["h"]
    style = s["style"]
    rnd = random.Random(s.get("seed") or 2026)
    colors = s["colors"]
    if style == "gradient":
        img = gradient_bg(w, h, colors)
        img = noise_dots(img, rnd)
        d = ImageDraw.Draw(img.convert("RGBA"))
        for _ in range(3):
            cx, cy = rnd.randint(0, w), rnd.randint(0, h)
            r = rnd.randint(min(w, h) // 12, min(w, h) // 5)
            col = lerp(hx(colors[0]), hx(colors[-1]), rnd.random())
            d.ellipse([cx - r, cy - r, cx + r, cy + r],
                      outline=(255, 255, 255, 60), width=max(2, w // 400))
        out = img.convert("RGB") if s["output"].lower().endswith((".jpg", ".jpeg")) else img.convert("RGBA")
    elif style == "poster":
        img = gradient_bg(w, h, colors)
        d = ImageDraw.Draw(img)
        d.rectangle([0, int(h * 0.82), w, h], fill=tuple(int(c * 0.55) for c in hx(colors[-1])))
        f, _ = fit_font(s.get("title", ""), int(w * 0.86), max(28, w // 14), fonts)
        if f:
            d.text((w // 2, int(h * 0.42)), s.get("title", ""), font=f, fill=(255, 255, 255),
                   anchor="mm", stroke_width=max(1, w // 800), stroke_fill=(0, 0, 0))
        if s.get("subtitle"):
            f2, _ = fit_font(s["subtitle"], int(w * 0.7), max(18, w // 28), fonts)
            if f2:
                d.text((w // 2, int(h * 0.60)), s["subtitle"], font=f2,
                       fill=(235, 235, 235), anchor="mm")
        d.rectangle([int(w * 0.42), int(h * 0.68), int(w * 0.58), int(h * 0.68) + max(4, h // 180)],
                    fill=(255, 255, 255))
        out = img
    elif style == "banner":
        img = Image.new("RGB", (w, h), tuple(hx(colors[-1])))
        d = ImageDraw.Draw(img, "RGBA")
        c0, c1 = hx(colors[0]), hx(colors[1])
        step = max(24, w // 22)
        for i in range(-h, w + h, step):
            t = (i + h) / (w + 2 * h)
            col = lerp(c0, c1, t)
            d.polygon([(i, 0), (i + step, 0), (i + step - h, h), (i - h, h)], fill=col + (170,))
        f, _ = fit_font(s.get("title", ""), int(w * 0.8), max(30, w // 10), fonts)
        if f:
            d.text((w // 2, h // 2), s.get("title", ""), font=f, fill=(255, 255, 255),
                   anchor="mm", stroke_width=max(1, w // 700), stroke_fill=(0, 0, 0))
        if s.get("subtitle"):
            f2, _ = fit_font(s["subtitle"], int(w * 0.6), max(16, w // 32), fonts)
            if f2:
                d.text((w // 2, int(h * 0.72)), s["subtitle"], font=f2, fill=(240, 240, 240), anchor="mm")
        out = img
    elif style == "avatar":
        m = min(w, h)
        img = gradient_bg(m, m, colors).resize((w, h))
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).ellipse([4, 4, w - 4, h - 4], fill=255)
        ch = (s.get("text") or "G").strip()[:2]
        d = ImageDraw.Draw(img)
        f, _ = fit_font(ch, int(m * 0.52), int(m * 0.5), fonts)
        if f:
            d.text((w // 2, h // 2), ch, font=f, fill=(255, 255, 255), anchor="mm")
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        out.paste(img, (0, 0), mask)
    else:  # card
        img = Image.new("RGB", (w, h), (250, 250, 250))
        d = ImageDraw.Draw(img, "RGBA")
        g = gradient_bg(w, max(24, h // 3), colors)
        img.paste(g, (0, 0))
        rnd = random.Random(s.get("seed") or 2026)
        for _ in range(4):
            cx, r = rnd.randint(0, w), rnd.randint(w // 14, w // 7)
            col = lerp(hx(colors[0]), hx(colors[-1]), rnd.random())
            d.ellipse([cx - r, -r, cx + r, r], fill=col + (140,))
        f, _ = fit_font(s.get("title", ""), int(w * 0.84), max(24, w // 16), fonts)
        if f:
            d.text((w // 2, int(h * 0.58)), s.get("title", ""), font=f, fill=(40, 40, 40), anchor="mm")
        if s.get("subtitle"):
            f2, _ = fit_font(s["subtitle"], int(w * 0.66), max(14, w // 30), fonts)
            if f2:
                d.text((w // 2, int(h * 0.72)), s["subtitle"], font=f2, fill=(110, 110, 110), anchor="mm")
        out = img
    if s["output"].lower().endswith((".jpg", ".jpeg")) and out.mode == "RGBA":
        out = out.convert("RGB")
    kw = {"quality": s["quality"]} if s.get("quality") else {}
    out.save(s["output"], **kw)
    print(json.dumps({"width": w, "height": h, "style": style}))
except Exception as e:
    import traceback
    print(json.dumps({"err": str(e), "tb": traceback.format_exc()[-300:]}, ensure_ascii=False))
    sys.exit(0)
'''


def eprint(msg):
    print(msg, file=sys.stderr)


def run_worker(spec):
    if importlib.util.find_spec("PIL") is not None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(spec, f)
            spec_path = f.name
        try:
            r = subprocess.run([sys.executable, "-c", WORKER, "--", spec_path],
                              capture_output=True, text=True, timeout=TIMEOUT)
        finally:
            os.unlink(spec_path)
    else:
        uv = shutil.which("uv")
        if not uv:
            return (None, "无 Pillow 亦无 uv：安装 uv（brew install uv）后本 CLI 即用即建临时环境")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(spec, f)
            spec_path = f.name
        try:
            r = subprocess.run([uv, "run", "--quiet", "--with", "pillow", "python", "-c",
                                WORKER, "--", spec_path],
                               capture_output=True, text=True, timeout=TIMEOUT,
                               env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        finally:
            os.unlink(spec_path)
    if r.returncode != 0:
        return (None, "生成进程失败：%s" % (r.stderr or r.stdout)[-400:])
    for line in (r.stdout or "").splitlines():
        try:
            d = json.loads(line.strip())
        except ValueError:
            continue
        if "err" in d:
            return (None, "生成报错：%s" % d.get("err"))
        return (d, None)
    return (None, "生成进程无有效输出：%s" % (r.stderr or r.stdout)[-300:])


def do_generate(args):
    if not args.output:
        eprint("用法错误：-o/--output 必须提供输出路径（扩展名决定格式）")
        return 1
    size = str(args.size or "1024x1024")
    if "x" not in size:
        eprint("用法错误：--size 需 '宽x高'（白名单：%s）" % ", ".join(SIZES))
        return 1
    try:
        w, h = (int(v) for v in size.lower().split("x", 1))
    except ValueError:
        eprint("用法错误：--size 需 '宽x高' 数字")
        return 1
    palette = (args.palette or "warm").lower()
    if palette not in PALETTES:
        eprint("用法错误：--palette 需为 %s" % "/".join(PALETTES))
        return 1
    if getattr(args, "title", None) or getattr(args, "subtitle", None):
        if args.style not in ("poster", "banner", "card") and args.style != "gradient":
            eprint("用法错误：--title/--subtitle 仅用于 poster/banner/card")
            return 1
    spec = {
        "w": w, "h": h, "style": args.style, "colors": PALETTES[palette],
        "title": getattr(args, "title", "") or "",
        "subtitle": getattr(args, "subtitle", "") or "",
        "text": getattr(args, "text", "") or "", "seed": args.seed,
        "output": args.output,
    }
    if args.quality:
        spec["quality"] = args.quality
    result, err = run_worker(spec)
    if result is None:
        eprint("[glmgenimg] 生成失败：%s" % err)
        return 2
    print("[glmgenimg] 已生成 %s（%sx%s，%s 风格，%s 调色板）"
          % (args.output, result.get("width"), result.get("height"),
             args.style, palette))
    if args.print_base64:
        try:
            with open(args.output, "rb") as f:
                print(base64.b64encode(f.read()).decode("ascii"))
        except BrokenPipeError:
            pass
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="glmgenimg.py",
        description="glm-image-generation：本地程序化生图 CLI（z-ai image 的等效替换）")
    sub = parser.add_subparsers(dest="style")

    def common(p, style):
        p.add_argument("-o", "--output", help="输出路径（扩展名决定格式）")
        p.add_argument("--size", help="'宽x高'（默认 1024x1024；白名单沿源 skill 7 档）")
        p.add_argument("--palette", default="warm",
                       help="调色板 %s（默认 warm）" % "/".join(PALETTES))
        p.add_argument("--seed", type=int, default=None, help="随机种子（可复现）")
        p.add_argument("--quality", type=int, help="JPEG 质量（0-95）")
        p.add_argument("--print-base64", action="store_true",
                       help="输出后打印 base64（对齐源响应 data[0].base64）")
        p.set_defaults(func=do_generate, style=style)

    p = sub.add_parser("gradient", help="渐变背景 + 几何元素")
    common(p, "gradient")
    for st, desc in [("poster", "标题海报"), ("banner", "斜纹横幅"),
                     ("avatar", "字母圆形头像"), ("card", "卡片封面")]:
        p = sub.add_parser(st, help=desc)
        p.add_argument("--title", help="主标题（poster/banner/card）")
        p.add_argument("--subtitle", help="副标题")
        p.add_argument("--text", help="avatar 内字母/短字")
        common(p, st)

    args = parser.parse_args()
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    try:
        return args.func(args)
    except KeyboardInterrupt:
        eprint("[glmgenimg] 已中断")
        return 1


if __name__ == "__main__":
    sys.exit(main())
