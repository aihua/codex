#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""track.py — glm-auto-target-tracker Codex 插件的本地目标打卡追踪 CLI。

等效替换源 skill（skills/auto-target-tracker）的两个外部依赖：

  1) 「vlm 工具」识别图片 → 本地 Ollama /api/chat 视觉链（images 传
     base64），按目标类型专用 prompt 出结构化
     JSON（任务清单/完成度/关键数据/反馈）。
  2) 「edit_daily 工具」写入当日笔记 → 本地 Markdown 目标日记
     （--journal 目录下 goal-journal/YYYY-MM-DD.md，追加条目）。

默认预览（stdout 打印拟记录条目），`--apply` 才落盘——对应源 skill
「反馈给用户确认后再记录」的流程。

用法：
  track.py ./notes.jpg                          # 自动判型，预览
  track.py ./gym.jpg --type fitness --json      # 指定健身类型，出 JSON
  track.py ./plan.png --type work --apply       # 确认后写入当日日记
  track.py ./habit.png --type habit --journal ./my-journal --apply
退出码：0 成功 / 1 用法错误 / 2 网络、图片或模型错误（stderr 报因，不假死）。
"""
import argparse
import base64
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_MODEL = os.environ.get("GLM_TRACK_MODEL", "gemma4:e4b")
DEFAULT_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
TIMEOUT = int(os.environ.get("GLM_TRACK_TIMEOUT", "600"))
MAX_IMAGE_MB = float(os.environ.get("GLM_TRACK_MAX_IMAGE_MB", "20"))

TYPE_META = {
    "study": ("📚 学习", "识别学习笔记/练习，提取知识点、任务与完成度、学习时长"),
    "fitness": ("🏃 健身", "识别健身记录，提取运动类型、组数、次数、重量与总训练量、时长"),
    "work": ("💼 工作", "识别工作进度截图，提取已完成/进行中/未开始任务与完成率"),
    "creative": ("🎨 创作", "识别创作作品，提取创作类型、关键元素、完成度"),
    "habit": ("✅ 习惯", "识别打卡日历/记录，提取打卡项、连续天数、打卡率"),
}
TYPE_EMOJI = {"study": "📚", "fitness": "🏃", "work": "💼", "creative": "🎨", "habit": "✅"}

PROMPT_HEAD = (
    "你是目标进度识别助手。分析图片，按目标类型提取关键信息，"
    "严格按以下 JSON 输出（不要多余文字）：\n"
    '{"type": "study|fitness|work|creative|habit",\n'
    ' "tasks": [{"content": string, "progress": string, "status": "已完成|进行中|未开始"}],\n'
    ' "key_data": [{"name": string, "value": string}],\n'
    ' "feedback": string}\n'
    "tasks 为任务/内容清单；key_data 为量化指标（时长/重量/字数/天数/百分比等）；"
    "feedback 为一句简短执行反馈。数值无法辨认时如实标 null。\n"
)


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
    t = text.strip()
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end <= start:
        return None
    for frag in (t, t[start:end + 1]):
        try:
            return json.loads(frag)
        except ValueError:
            continue
    return None


def build_prompt(goal_type, images):
    prompt = PROMPT_HEAD
    if goal_type in TYPE_META:
        _, hint = TYPE_META[goal_type]
        prompt += "目标类型固定为 %s。%s。\n" % (goal_type, hint)
    else:
        prompt += "目标类型由你根据图片内容判断（study/fitness/work/creative/habit）。\n"
    if len(images) > 1:
        prompt += "共 %d 张图片，按 [图1]…[图%d] 归并进同一 JSON。\n" % (len(images), len(images))
    prompt += "只输出 JSON。"
    return prompt


def render_markdown(d, images, goal_type):
    now = datetime.datetime.now()
    t = d.get("type") or goal_type or "unknown"
    emoji = TYPE_EMOJI.get(t, "📝")
    lines = []
    lines.append("## %s 打卡记录" % now.strftime("%H:%M"))
    lines.append("")
    lines.append("**目标类型**: %s %s" % (emoji, {"study": "学习", "fitness": "健身", "work": "工作",
                                                "creative": "创作", "habit": "习惯"}.get(t, t)))
    for i, img in enumerate(images, 1):
        lines.append("")
        lines.append("**图片**: ![目标图片%d](%s)" % (i if len(images) > 1 else 0, img))
    lines.append("")
    lines.append("**识别结果**:")
    lines.append("")
    tasks = d.get("tasks") or []
    if tasks:
        lines.append("| 任务/内容 | 进度/数量 | 状态 |")
        lines.append("|---|---|---|")
        for tk in tasks:
            if isinstance(tk, dict):
                lines.append("| %s | %s | %s |" % (tk.get("content", ""), tk.get("progress", ""),
                                                   tk.get("status", "")))
            else:
                lines.append("| %s | | |" % tk)
    kd = d.get("key_data") or []
    if kd:
        lines.append("")
        lines.append("**关键数据**:")
        for kv in kd:
            if isinstance(kv, dict):
                lines.append("- %s: %s" % (kv.get("name", ""), kv.get("value", "")))
            else:
                lines.append("- %s" % kv)
    if d.get("feedback"):
        lines.append("")
        lines.append("**反馈**: %s" % d["feedback"])
    lines.append("")
    lines.append("**备注**: 自动识别（glm-auto-target-tracker），请核对后修正")
    lines.append("")
    return "\n".join(lines)


def do_track(args):
    if not args.images:
        eprint("用法错误：至少提供一张图片路径")
        return 1
    if args.type and args.type not in list(TYPE_META) + ["auto"]:
        eprint("用法错误：--type 需为 %s 或 auto" % "/".join(TYPE_META))
        return 1
    b64s = []
    for src in args.images:
        b64, err = load_image_b64(src)
        if b64 is None:
            eprint("[track] %s" % err)
            return 2
        b64s.append(b64)

    goal_type = None if (not args.type or args.type == "auto") else args.type
    prompt = build_prompt(goal_type, args.images)
    messages = [{"role": "user", "content": prompt, "images": b64s}]

    status, payload = post_chat(args.model, messages, timeout=args.timeout)
    if status != "ok":
        low = str(payload).lower()
        if "model not found" in low:
            eprint("[track] 模型不存在：%s。先执行: ollama pull %s" % (args.model, args.model))
        elif "image" in low and "error" in low:
            eprint("[track] 模型 %s 不支持图像；视觉任务用多模态模型" % args.model)
        eprint("[track] 失败: %s" % payload)
        return 2

    content = ((payload.get("message") or {}).get("content")) or ""
    d = parse_json_loose(content)
    if d is None:
        d = {"type": goal_type or "unknown", "tasks": [], "key_data": [],
             "feedback": content.strip()[:300], "raw": content}
    if goal_type and d.get("type") != goal_type:
        d["type"] = goal_type
    if args.json:
        out = {"success": True, "type": d.get("type"), "model": args.model,
               "images": args.images, "parsed": d}
        print(json.dumps(out, ensure_ascii=False, indent=2))

    md = render_markdown(d, args.images, goal_type)
    if args.apply:
        journal_dir = args.journal
        os.makedirs(journal_dir, exist_ok=True)
        path = os.path.join(journal_dir, datetime.date.today().strftime("%Y-%m-%d") + ".md")
        header = ""
        if not os.path.exists(path):
            header = "# 目标日记 %s\n\n" % datetime.date.today().strftime("%Y-%m-%d")
        with open(path, "a", encoding="utf-8") as f:
            f.write(header + md + "\n---\n\n")
        print("[track] 已记录到 %s（type=%s，tasks=%d）" % (path, d.get("type"), len(d.get("tasks") or [])))
    else:
        print(md)
        print("[track] 预览模式（未落盘）。确认无误后加 --apply 写入 %s/"
              "%s.md" % (args.journal, datetime.date.today().strftime("%Y-%m-%d")))
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="track.py",
        description="glm-auto-target-tracker：本地目标打卡追踪 CLI（vlm 工具 + edit_daily 的等效替换）")
    parser.add_argument("images", nargs="+", help="图片路径（可多张）")
    parser.add_argument("--type", default="auto",
                        help="study|fitness|work|creative|habit|auto（默认 auto 自动判型）")
    parser.add_argument("--journal", default="goal-journal", help="目标日记目录（默认 ./goal-journal）")
    parser.add_argument("--apply", action="store_true", help="写入当日日记（默认仅预览）")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help="视觉模型名（默认 %s）" % DEFAULT_MODEL)
    parser.add_argument("--json", action="store_true", help="同时输出结构化 JSON")
    parser.add_argument("--timeout", type=int, default=TIMEOUT,
                        help="HTTP 超时秒数（默认 %d）" % TIMEOUT)
    args = parser.parse_args()
    try:
        return do_track(args)
    except KeyboardInterrupt:
        eprint("[track] 已中断")
        return 1


if __name__ == "__main__":
    sys.exit(main())
