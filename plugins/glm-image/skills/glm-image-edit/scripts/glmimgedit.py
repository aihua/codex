#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""glmimgedit.py — glm-image-edit Codex 插件的本地图像编辑 CLI。

等效替换源 skill（skills/image-edit）对 z-ai-web-dev-sdk
`zai.images.generations.edit({prompt, images, size})` 与 `z-ai image-edit`
CLI 的调用。本地不部署该 SDK，且 Ollama 文本模型无法做图像编辑——等效为
**Pillow 确定性编辑管线**（uv 即用即建临时环境承载，或系统 python3 已装
PIL 时直接进程内执行）：

  支持的确定性操作：裁剪/居中裁剪、缩放（含源 skill 的 7 个尺寸）、旋转、
  翻转、灰度、模糊/锐化、亮度/对比度/饱和度、白边裁剪、衬边留黑、加边框、
  文字水印/任意位置标注、图片合成、格式转换。

  语义级 AI 编辑（"把猫换成狗"）本地链不做：见 SKILL.md 的诚实降级说明
  （需要扩散模型服务，建议路由 ComfyUI/SD WebUI 等外部工具）。

用法：
  glmimgedit.py edit -i in.png -o out.png --resize 1024x1024 --grayscale
  glmimgedit.py edit -i in.jpg -o square.jpg --crop-center 80%
  glmimgedit.py edit -i in.png -o wm.png --watermark "© Z.ai" --corner br
  glmimgedit.py info -i in.png
  glmimgedit.py edit -i in.png -o out.jpg --print-base64     # 源响应 base64 对齐
退出码：0 成功 / 1 用法错误 / 2 后端缺失或编辑失败（stderr 报因，不假死）。
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
import urllib.request

SIZES = ["1024x1024", "768x1344", "864x1152", "1344x768", "1152x864",
         "1440x720", "720x1440"]  # 沿源 skill 的支持尺寸白名单
TIMEOUT = int(os.environ.get("GLM_IMGEDIT_TIMEOUT", "300"))

WORKER = r'''
import json, sys
_a = sys.argv[1:]
if _a and _a[0] == "--": _a = _a[1:]
spec = json.load(open(_a[0]))
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps
try:
    img = Image.open(spec["input"])
    img.load()
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    for op in spec.get("ops", []):
        k = op.get("op")
        if k == "trim":
            from PIL import ImageChops
            bg = Image.new(img.mode, img.size, (255, 255, 255) if img.mode == "RGB" else (255, 255, 255, 0))
            diff = ImageChops.difference(img, bg)
            bbox = diff.getbbox()
            if bbox: img = img.crop(bbox)
        elif k == "crop":
            img = img.crop((op["left"], op["top"], op["right"], op["bottom"]))
        elif k == "crop_center":
            pct = op["pct"]
            w, h = img.size
            nw, nh = max(1, int(w * pct / 100)), max(1, int(h * pct / 100))
            img = img.crop(((w - nw) // 2, (h - nh) // 2, (w + nw) // 2, (h + nh) // 2))
        elif k == "resize":
            img = img.resize((op["w"], op["h"]), Image.LANCZOS)
        elif k == "fit":
            img.thumbnail((op["w"], op["h"]), Image.LANCZOS)
        elif k == "rotate":
            img = img.rotate(op["deg"], expand=bool(op.get("expand", True)),
                             resample=Image.BICUBIC, fillcolor=(255, 255, 255) if img.mode == "RGB" else (255, 255, 255, 0))
        elif k == "flip":
            img = img.transpose(Image.FLIP_TOP_BOTTOM if op["axis"] == "v" else Image.FLIP_LEFT_RIGHT)
        elif k == "grayscale":
            img = img.convert("L")
        elif k == "blur":
            from PIL import ImageFilter
            img = img.filter(ImageFilter.GaussianBlur(op["radius"]))
        elif k == "sharpen":
            img = ImageEnhance.Sharpness(img).enhance(op["factor"])
        elif k == "brightness":
            img = ImageEnhance.Brightness(img).enhance(op["factor"])
        elif k == "contrast":
            img = ImageEnhance.Contrast(img).enhance(op["factor"])
        elif k == "saturate":
            img = ImageEnhance.Color(img).enhance(op["factor"])
        elif k == "pad":
            w, h = op["w"], op["h"]
            bg = Image.new("RGB" if img.mode == "L" or img.mode == "RGB" else "RGBA", (w, h), tuple(op.get("color", (255, 255, 255))))
            bg.paste(img, ((w - img.width) // 2, (h - img.height) // 2))
            img = bg
        elif k == "border":
            from PIL import ImageOps
            img = ImageOps.expand(img, border=op["size"], fill=tuple(op.get("color", (0, 0, 0))))
        elif k in ("watermark", "annotate"):
            draw = ImageDraw.Draw(img)
            fs = op.get("size", 36)
            font = None
            for fp in ("/System/Library/Fonts/PingFang.ttc",
                       "/System/Library/Fonts/Hiragino Sans GB.ttc",
                       "/System/Library/Fonts/Supplemental/Songti.ttc",
                       "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
                try:
                    font = ImageFont.truetype(fp, fs); break
                except Exception:
                    continue
            if font is None:
                try: font = ImageFont.load_default()
                except Exception: font = None
            color = tuple(op.get("color", (255, 255, 255)))
            text = op.get("text", "")
            if k == "watermark":
                if img.mode != "RGBA":
                    from PIL import Image as I
                    layer = I.new("RGBA", img.size, (0, 0, 0, 0))
                    d2 = ImageDraw.Draw(layer)
                    anchor = {"tl": "lt", "tr": "rt", "bl": "lb", "br": "rb", "center": "mm"}[op.get("corner", "br")]
                    d2.text((10, 10) if op.get("corner", "br") != "center" else (img.width // 2, img.height // 2),
                            text, font=font, fill=color + (int(op.get("opacity", 200) * 255 / 100),), anchor=anchor)
                    img = I.alpha_composite(img.convert("RGBA"), layer)
                    if spec.get("output", "").lower().endswith((".jpg", ".jpeg")):
                        img = img.convert("RGB")
                else:
                    draw = ImageDraw.Draw(img)
                    anchor = {"tl": "lt", "tr": "rt", "bl": "lb", "br": "rb", "center": "mm"}[op.get("corner", "br")]
                    draw.text((10, 10), text, font=font, fill=color, anchor=anchor)
            else:
                draw.text((op.get("x", 10), op.get("y", 10)), text, font=font, fill=color)
        elif k == "composite":
            ov = Image.open(op["overlay"]); ov.load()
            if ov.mode != "RGBA":
                ov = ov.convert("RGBA")
            if op.get("opacity", 100) < 100:
                alpha = ov.getchannel("A").point(lambda a: int(a * op["opacity"] / 100))
                ov.putalpha(alpha)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img.alpha_composite(ov, dest=(op.get("x", 0), op.get("y", 0)))
    save_kw = {}
    if spec.get("quality"): save_kw["quality"] = spec["quality"]
    fmt = spec.get("format")
    if fmt: save_kw["format"] = fmt
    out = spec.get("output", "").lower()
    if out.endswith((".jpg", ".jpeg")) and img.mode == "RGBA":
        img = img.convert("RGB")
    img.save(spec["output"], **save_kw)
    print(json.dumps({"width": img.width, "height": img.height}))
except Exception as e:
    print(json.dumps({"err": str(e)}, ensure_ascii=False))
    sys.exit(0)
'''


def eprint(msg):
    print(msg, file=sys.stderr)


def parse_size(s):
    s = str(s).strip().lower()
    if "x" not in s:
        return None
    try:
        w, h = s.split("x", 1)
        return (int(w), int(h))
    except ValueError:
        return None


def fetch_input(path):
    if path.startswith("http://") or path.startswith("https://"):
        tmp = tempfile.NamedTemporaryFile(prefix="glmedit_", suffix=os.path.splitext(path)[1] or ".img",
                                           delete=False)
        req = urllib.request.Request(path, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            tmp.write(r.read())
        tmp.close()
        return tmp.name, True
    return path, False


def run_worker(spec):
    """优先进程内 PIL；否则 uv run --with pillow。返回 (dict|None, err|None)。"""
    if importlib.util.find_spec("PIL") is not None:
        code = WORKER
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(spec, f)
            spec_path = f.name
        try:
            r = subprocess.run([sys.executable, "-c", code, "--", spec_path],
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
            r = subprocess.run([uv, "run", "--quiet", "--with", "pillow", "python", "-c", code,
                                "--", spec_path],
                               capture_output=True, text=True, timeout=TIMEOUT,
                               env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        finally:
            os.unlink(spec_path)
    if r.returncode != 0:
        return (None, "编辑进程失败：%s" % (r.stderr or r.stdout)[-400:])
    for line in (r.stdout or "").splitlines():
        try:
            d = json.loads(line.strip())
        except ValueError:
            continue
        if "err" in d:
            return (None, "Pillow 报错：%s" % d["err"])
        return (d, None)
    return (None, "编辑进程无有效输出：%s" % (r.stderr or r.stdout)[-300:])


def build_ops(args):
    ops = []
    if args.trim:
        ops.append({"op": "trim"})
    if args.crop:
        parts = [int(v) for v in str(args.crop).split(",")]
        if len(parts) != 4:
            eprint("用法错误：--crop 需 '左,上,右,下' 像素四元组")
            return None
        ops.append({"op": "crop", "left": parts[0], "top": parts[1],
                    "right": parts[2], "bottom": parts[3]})
    if args.crop_center:
        pct = str(args.crop_center).rstrip("%")
        if not pct.replace(".", "", 1).isdigit():
            eprint("用法错误：--crop-center 需百分比（如 80）")
            return None
        ops.append({"op": "crop_center", "pct": float(pct)})
    if args.rotate:
        ops.append({"op": "rotate", "deg": float(args.rotate)})
    if args.flip:
        ops.append({"op": "flip", "axis": args.flip})
    if args.resize:
        wh = parse_size(args.resize)
        if not wh:
            eprint("用法错误：--resize 需 '宽x高'（如 1024x1024；源尺寸白名单见 SKILL.md）")
            return None
        ops.append({"op": "resize", "w": wh[0], "h": wh[1]})
    if args.fit:
        wh = parse_size(args.fit)
        if not wh:
            eprint("用法错误：--fit 需 '宽x高'（保持纵横比缩放到框内）")
            return None
        ops.append({"op": "fit", "w": wh[0], "h": wh[1]})
    if args.grayscale:
        ops.append({"op": "grayscale"})
    if args.blur:
        ops.append({"op": "blur", "radius": float(args.blur)})
    if args.sharpen:
        ops.append({"op": "sharpen", "factor": float(args.sharpen)})
    if args.brightness:
        ops.append({"op": "brightness", "factor": float(args.brightness)})
    if args.contrast:
        ops.append({"op": "contrast", "factor": float(args.contrast)})
    if args.saturate:
        ops.append({"op": "saturate", "factor": float(args.saturate)})
    if args.pad:
        wh = parse_size(args.pad)
        if not wh:
            eprint("用法错误：--pad 需 '宽x高'")
            return None
        ops.append({"op": "pad", "w": wh[0], "h": wh[1], "color": [255, 255, 255]})
    if args.border:
        if not str(args.border).isdigit():
            eprint("用法错误：--border 需像素宽度")
            return None
        ops.append({"op": "border", "size": int(args.border), "color": [0, 0, 0]})
    if args.watermark:
        ops.append({"op": "watermark", "text": args.watermark, "corner": args.corner,
                    "size": args.font_size, "opacity": 70})
    if args.annotate:
        ops.append({"op": "annotate", "text": args.annotate, "x": args.x, "y": args.y,
                    "size": args.font_size})
    if args.composite:
        for pth in [args.composite]:
            if not os.path.exists(pth):
                eprint("用法错误：--composite 叠加图不存在 %s" % pth)
                return None
        ops.append({"op": "composite", "overlay": args.composite,
                    "x": args.x, "y": args.y, "opacity": args.opacity})
    return ops


def do_edit(args):
    if not args.input:
        eprint("用法错误：-i/--input 必须提供源图（本地路径或 http(s) URL）")
        return 1
    if not args.output:
        eprint("用法错误：-o/--output 必须提供输出路径")
        return 1
    ops = build_ops(args)
    if ops is None:
        return 1
    if not ops:
        eprint("用法错误：至少指定一个编辑操作（--resize/--crop/--grayscale/--watermark 等）")
        return 1
    path, is_temp = fetch_input(args.input)
    if not os.path.exists(path):
        eprint("[glmimgedit] 源图不存在或下载失败：%s" % args.input)
        return 2
    spec = {"input": path, "output": args.output, "ops": ops}
    if args.quality:
        spec["quality"] = args.quality
    try:
        result, err = run_worker(spec)
        if result is None:
            eprint("[glmimgedit] 编辑失败：%s" % err)
            return 2
        print("[glmimgedit] 已生成 %s（%sx%s，%d 个操作）"
              % (args.output, result.get("width"), result.get("height"), len(ops)))
        if args.print_base64:
            try:
                with open(args.output, "rb") as f:
                    print(base64.b64encode(f.read()).decode("ascii"))
            except BrokenPipeError:
                pass  # 下游提前关闭管道（如 head 截断），不算失败
        return 0
    finally:
        if is_temp and os.path.exists(path):
            os.unlink(path)


def do_info(args):
    if not args.input:
        eprint("用法错误：-i/--input 必须提供图片")
        return 1
    path, is_temp = fetch_input(args.input)
    if not os.path.exists(path):
        eprint("[glmimgedit] 图片不存在或下载失败：%s" % args.input)
        return 2
    spec = {"input": path, "output": os.devnull, "ops": []}
    probe = r'''
import json, sys
_a = sys.argv[1:]
if _a and _a[0] == "--": _a = _a[1:]
try:
    from PIL import Image
    im = Image.open(_a[0]); im.load()
    print(json.dumps({"width": im.width, "height": im.height,
                     "format": im.format, "mode": im.mode}))
except Exception as e:
    print(json.dumps({"err": str(e)}))
'''
    uv = shutil.which("uv")
    try:
        if importlib.util.find_spec("PIL") is not None:
            r = subprocess.run([sys.executable, "-c", probe, path], capture_output=True, text=True, timeout=60)
        elif uv:
            r = subprocess.run([uv, "run", "--quiet", "--with", "pillow", "python", "-c", probe, "--", path],
                               capture_output=True, text=True, timeout=120)
        else:
            eprint("[glmimgedit] 无 Pillow 亦无 uv：brew install uv 后可用")
            return 2
        for line in (r.stdout or "").splitlines():
            try:
                d = json.loads(line.strip())
            except ValueError:
                continue
            if "err" in d:
                eprint("[glmimgedit] 打开失败：%s" % d["err"])
                return 2
            print(json.dumps(d, ensure_ascii=False))
            return 0
        eprint("[glmimgedit] 探测无输出")
        return 2
    finally:
        if is_temp and os.path.exists(path):
            os.unlink(path)


def main():
    parser = argparse.ArgumentParser(
        prog="glmimgedit.py",
        description="glm-image-edit：本地确定性图像编辑 CLI（z-ai image-edit 的等效替换）")
    sub = parser.add_subparsers(dest="cmd")

    e = sub.add_parser("edit", help="按操作管线编辑图片")
    e.add_argument("-i", "--input", help="源图（本地路径或 http(s) URL）")
    e.add_argument("-o", "--output", help="输出路径（扩展名决定格式）")
    e.add_argument("--trim", action="store_true", help="裁掉纯色白边")
    e.add_argument("--crop", help="像素裁剪 '左,上,右,下'")
    e.add_argument("--crop-center", help="居中百分比裁剪（如 80）")
    e.add_argument("--resize", help="精确缩放 '宽x高'（支持源 skill 白名单 7 尺寸）")
    e.add_argument("--fit", help="保持纵横比缩进 '宽x高' 框")
    e.add_argument("--rotate", help="旋转角度（顺时针为负，逆时针为正）")
    e.add_argument("--flip", choices=["h", "v"], help="水平/垂直翻转")
    e.add_argument("--grayscale", action="store_true", help="灰度化")
    e.add_argument("--blur", help="高斯模糊半径")
    e.add_argument("--sharpen", help="锐化因子（1.0 原样，>1 增强）")
    e.add_argument("--brightness", help="亮度因子（1.0 原样）")
    e.add_argument("--contrast", help="对比度因子")
    e.add_argument("--saturate", help="饱和度因子")
    e.add_argument("--pad", help="衬底到 '宽x高'（白底居中）")
    e.add_argument("--border", help="加黑色边框（像素宽）")
    e.add_argument("--watermark", help="右下角等角落文字水印")
    e.add_argument("--corner", default="br", choices=["tl", "tr", "bl", "br", "center"],
                   help="水印角落（默认 br）")
    e.add_argument("--annotate", help="任意位置文字标注")
    e.add_argument("--composite", help="叠加另一张图（路径）")
    e.add_argument("--x", type=int, default=10, help="标注/叠加 X 坐标")
    e.add_argument("--y", type=int, default=10, help="标注/叠加 Y 坐标")
    e.add_argument("--opacity", type=int, default=100, help="叠加不透明度 0-100")
    e.add_argument("--font-size", type=int, default=36, help="水印/标注字号")
    e.add_argument("--quality", type=int, help="JPEG 质量（0-95）")
    e.add_argument("--print-base64", action="store_true", help="输出后打印 base64（对齐源响应 data[0].base64）")
    e.set_defaults(func=do_edit)

    n = sub.add_parser("info", help="查看图片宽高/格式")
    n.add_argument("-i", "--input", help="图片路径或 URL")
    n.set_defaults(func=do_info)

    args = parser.parse_args()
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    try:
        return args.func(args)
    except KeyboardInterrupt:
        eprint("[glmimgedit] 已中断")
        return 1


if __name__ == "__main__":
    sys.exit(main())
