#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""glmimgund.py — glm-image-understand Codex 插件的本地图像理解 CLI。

等效替换源 skill（skills/image-understand）对 z-ai-web-dev-sdk
`zai.chat.completions.createVision()` 与 `z-ai vision` CLI 的调用（静态图像
分析向）：本地不部署该 SDK，改经 Ollama 原生 /api/chat（images 传 base64）
完成。

与 glm-vlm（视觉「对话」）的分工：本插件面向「分析任务」——内置 OCR、
分类、对象清单、alt 文本、质量评估、差异对比等专用 prompt 模板与结构化
JSON 输出。

纯 Python 标准库，零 pip 依赖。

用法：
  glmimgund.py ocr -i ./doc.png                       # 文字提取
  glmimgund.py classify -i ./photo.jpg --json          # 分类打标
  glmimgund.py alttext -i ./banner.png                 # 无障碍替代文本
  glmimgund.py objects -i ./shelf.jpg                  # 对象清单与计数
  glmimgund.py quality -i ./photo.jpg                  # 质量评估
  glmimgund.py diff -i a.png -i b.png                  # 多图差异
  glmimgund.py custom -i ./x.png -p "自定义问题"        # 自定义分析
退出码：0 成功 / 1 用法错误 / 2 网络、图片或模型错误（stderr 报因，不假死）。
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_MODEL = os.environ.get("GLM_IMGUND_MODEL", "gemma4:e4b")
DEFAULT_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
TIMEOUT = int(os.environ.get("GLM_IMGUND_TIMEOUT", "600"))
MAX_IMAGE_MB = float(os.environ.get("GLM_IMGUND_MAX_IMAGE_MB", "20"))

TASKS = {
    "ocr": ("识别图片中的全部文字，尽量保留原有版面结构与换行；无法辨认的字符用□标记。"
            "仅输出文字内容本身。", "plain"),
    "classify": ("分析这张图片，严格按以下 JSON 输出（不要多余文字）："
                 "{\"main_subject\": string, \"category\": string, "
                 "\"key_objects\": string[], \"scene\": string, "
                 "\"tags\": string[]}（tags 为中文短标签数组，5-8 个）。", "json"),
    "alttext": ("为这张图片生成一句无障碍替代文本（alt text）：中文，不超过 40 字，"
                "描述核心内容与关键元素。仅输出这句话。", "plain"),
    "objects": ("列出图中可辨认的对象清单。严格按 JSON 输出（不要多余文字）："
                "{\"objects\": [{\"name\": string, \"count\": number, "
                "\"detail\": string}]}；无法计数的 count 填 null。", "json"),
    "quality": ("从清晰度、曝光、构图、色彩、可辨识缺陷五个方面评估这张图片。"
                "严格按 JSON 输出（不要多余文字）：{\"sharpness\": string, "
                "\"exposure\": string, \"composition\": string, "
                "\"color\": string, \"defects\": string[], "
                "\"overall\": \"优|良|中|差\"}。", "json"),
    "diff": ("逐区域对比这几张图片的异同。严格按 JSON 输出（不要多余文字）："
             "{\"same_summary\": string, \"differences\": [{\"region\": string, "
             "\"description\": string}]}。", "json"),
}


def eprint(msg):
    print(msg, file=sys.stderr)


def host_url(path):
    host = DEFAULT_HOST.rstrip("/")
    if not (host.startswith("http://") or host.startswith("https://")):
        host = "http://" + host
    return host + path


def load_image_b64(source):
    try:
        if source.startswith("http://") or source.startswith("https://"):
            req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
        else:
            with open(source, "rb") as f:
                data = f.read()
    except (urllib.error.URLError, OSError) as e:
        return (None, "无法读取图片 %s (%s)" % (source, e))
    if len(data) > MAX_IMAGE_MB * 1024 * 1024:
        return (None, "图片过大 %s（%.1fMB > %.0fMB 上限）" % (source, len(data) / 1048576, MAX_IMAGE_MB))
    return (base64.b64encode(data).decode("ascii"), None)


def post_chat(model, messages, timeout=TIMEOUT):
    body = {"model": model, "messages": messages, "stream": False}
    req = urllib.request.Request(
        host_url("/api/chat"),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return ("ok", json.loads(resp.read().decode("utf-8", "replace")))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", "replace")[:400]
        except Exception:
            detail = ""
        return ("http_error", "HTTP %s: %s" % (e.code, detail or e.reason))
    except (urllib.error.URLError, OSError, ValueError) as e:
        return ("net_error", "cannot reach Ollama at %s (%s)" % (host_url("/api/chat"), e))


def parse_json_loose(text):
    """小模型常在 JSON 外包裹话术——尽力剥出首个 JSON 对象。"""
    t = text.strip()
    if t.startswith("{"):
        try:
            return json.loads(t)
        except ValueError:
            pass
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(t[start:end + 1])
        except ValueError:
            return None
    return None


def do_analyze(args):
    task = getattr(args, "task", "custom")
    images = getattr(args, "image", []) or []
    if task == "custom" and not (args.prompt and args.prompt.strip()):
        eprint("用法错误：custom 任务必须用 -p 提供分析问题")
        return 1
    if not images:
        eprint("用法错误：-i/--image 至少提供一张图片（本地路径或 http(s) URL）")
        return 1
    if task == "diff" and len(images) < 2:
        eprint("用法错误：diff 任务至少需要两张图片")
        return 1

    b64s = []
    for src in images:
        b64, err = load_image_b64(src)
        if b64 is None:
            eprint("[glmimgund] %s" % err)
            return 2
        b64s.append(b64)

    if task == "custom":
        prompt_tpl, fmt = args.prompt, "plain"
    else:
        prompt_tpl, fmt = TASKS[task]
    if len(b64s) > 1 and task != "diff":
        prompt_tpl += "（共 %d 张图，请依次分析并在输出中用 [图1]…[图%d] 标注对应关系。）" % (
            len(b64s), len(b64s))
    messages = [{"role": "user", "content": prompt_tpl, "images": b64s}]

    status, payload = post_chat(args.model, messages, timeout=args.timeout)
    if status != "ok":
        low = str(payload).lower()
        if "model not found" in low:
            eprint("[glmimgund] 模型不存在：%s。先执行: ollama pull %s" % (args.model, args.model))
        elif "image" in low and "error" in low:
            eprint("[glmimgund] 模型 %s 不支持图像输入；视觉任务请用多模态模型" % args.model)
        eprint("[glmimgund] 失败: %s" % payload)
        return 2

    content = ((payload.get("message") or {}).get("content")) or ""
    if not content.strip():
        eprint("[glmimgund] 模型返回空内容；重试或换更具体的任务")
        return 2

    out = {"success": True, "task": task, "model": args.model, "images": len(b64s)}
    if fmt == "json" or args.json:
        parsed = parse_json_loose(content)
        out["result"] = parsed if parsed is not None else {"raw": content}
        if parsed is None:
            out["parse_warning"] = "模型输出非严格 JSON，已附 raw 文本"
        text = json.dumps(out, ensure_ascii=False, indent=2)
    else:
        out["text"] = content
        text = content if not args.json else json.dumps(out, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text if (fmt == "json" or args.json) else text)
        print("[glmimgund] 已写入 %s" % args.output)
    else:
        print(text)
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="glmimgund.py",
        description="glm-image-understand：本地 Ollama 静态图像分析 CLI（z-ai vision 分析向的等效替换）")
    sub = parser.add_subparsers(dest="task")

    def common(p):
        p.add_argument("-i", "--image", action="append", default=[],
                       help="图片路径或 http(s) URL（可重复传多张）")
        p.add_argument("--model", default=DEFAULT_MODEL,
                       help="多模态模型名（默认 %s）" % DEFAULT_MODEL)
        p.add_argument("--json", action="store_true", help="强制 JSON 输出")
        p.add_argument("-o", "--output", help="把结果写入该路径")
        p.add_argument("--timeout", type=int, default=TIMEOUT,
                       help="HTTP 超时秒数（默认 %d）" % TIMEOUT)
        p.set_defaults(func=do_analyze)

    for task in list(TASKS) + ["custom"]:
        p = sub.add_parser(task, help="%s 任务" % task)
        if task == "custom":
            p.add_argument("-p", "--prompt", help="自定义分析问题")
        common(p)

    args = parser.parse_args()
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    try:
        return args.func(args)
    except KeyboardInterrupt:
        eprint("[glmimgund] 已中断")
        return 1


if __name__ == "__main__":
    sys.exit(main())
