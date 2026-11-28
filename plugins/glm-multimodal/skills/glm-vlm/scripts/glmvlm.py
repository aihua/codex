#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""glmvlm.py — glm-vlm Codex 插件的本地视觉对话 CLI。

等效替换源 skill（skills/VLM）对 z-ai-web-dev-sdk
`zai.chat.completions.createVision()` 与 `z-ai vision` CLI 的调用：本地不部署
该 SDK，全部能力改经 Ollama 原生 /api/chat 端点（messages[].images 传 base64）
完成。默认模型可用 GLM_VLM_MODEL 环境变量或 --model 参数覆盖
--model 切换。

纯 Python 标准库，零 pip 依赖。

用法：
  glmvlm.py -p "描述这张图" -i ./photo.jpg            # 本地图片
  glmvlm.py -p "..." -i https://example.com/a.png     # URL 图片（自动下载）
  glmvlm.py -p "对比这两张图" -i a.jpg -i b.jpg        # 多图
  glmvlm.py -p "..." -i x.jpg --session v.jsonl        # 视觉多轮会话
  glmvlm.py -p "..." -i x.jpg --json -o out.json       # SDK 兼容 JSON
退出码：0 成功 / 1 用法错误 / 2 网络、图片或模型服务错误（stderr 报因，不假死）。
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_MODEL = os.environ.get("GLM_VLM_MODEL", "gemma4:e4b")
DEFAULT_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
TIMEOUT = int(os.environ.get("GLM_VLM_TIMEOUT", "600"))
MAX_IMAGE_MB = float(os.environ.get("GLM_VLM_MAX_IMAGE_MB", "20"))


def eprint(msg):
    print(msg, file=sys.stderr)


def host_url(path):
    host = DEFAULT_HOST.rstrip("/")
    if not (host.startswith("http://") or host.startswith("https://")):
        host = "http://" + host
    return host + path


def guess_mime(path_or_url):
    low = path_or_url.lower()
    for ext, mt in ((".png", "image/png"), (".jpg", "image/jpeg"), (".jpeg", "image/jpeg"),
                    (".gif", "image/gif"), (".webp", "image/webp"), (".bmp", "image/bmp")):
        if low.endswith(ext):
            return mt
    return "image/jpeg"


def load_image_b64(source):
    """本地路径或 http(s) URL → base64 字符串（失败返回 None, reason）。"""
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


def load_history(session_path):
    if not session_path or not os.path.exists(session_path):
        return []
    msgs = []
    with open(session_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                m = json.loads(line)
                if isinstance(m, dict) and m.get("role") and m.get("content") is not None:
                    msgs.append({"role": m["role"], "content": m["content"]})
            except ValueError:
                continue
    return msgs


def append_history(session_path, role, content):
    if not session_path:
        return
    with open(session_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"role": role, "content": content}, ensure_ascii=False) + "\n")


def do_vision(args):
    if not args.prompt or not args.prompt.strip():
        eprint("用法错误：-p/--prompt 必须提供关于图片的指令")
        return 1
    if not args.image:
        eprint("用法错误：-i/--image 至少提供一张图片（本地路径或 http(s) URL）")
        return 1

    b64s = []
    for src in args.image:
        b64, err = load_image_b64(src)
        if b64 is None:
            eprint("[glmvlm] %s" % err)
            return 2
        b64s.append(b64)

    messages = load_history(args.session)
    user_msg = {"role": "user", "content": str(args.prompt), "images": b64s}
    messages.append(user_msg)

    status, payload = post_chat(args.model, messages, timeout=args.timeout)
    if status != "ok":
        low = str(payload).lower()
        if "model not found" in low:
            eprint("[glmvlm] 模型不存在：%s。先执行: ollama pull %s" % (args.model, args.model))
        elif "does not support images" in low or "image" in low and "error" in low:
            eprint("[glmvlm] 模型 %s 似乎不支持图像输入。视觉任务请用多模态模型：" % args.model)
            eprint("        ollama pull <多模态模型> && glmvlm.py --model <多模态模型> …")
        eprint("[glmvlm] 失败: %s" % payload)
        eprint("[glmvlm] 检查: ollama serve 是否运行 / OLLAMA_HOST / 模型是否多模态")
        return 2

    content = ((payload.get("message") or {}).get("content")) or ""
    append_history(args.session, "user", str(args.prompt))
    append_history(args.session, "assistant", content)

    if args.json:
        out = {
            "success": True,
            "model": args.model,
            "images": len(b64s),
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content},
                         "finish_reason": "stop"}],
        }
        text = json.dumps(out, ensure_ascii=False, indent=2)
    else:
        text = content
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print("[glmvlm] 已写入 %s" % args.output)
    else:
        print(text)
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="glmvlm.py",
        description="glm-vlm：本地 Ollama 视觉对话 CLI（z-ai vision 的等效替换）")
    parser.add_argument("-p", "--prompt", required=True, help="关于图片的指令/问题")
    parser.add_argument("-i", "--image", action="append", default=[],
                        help="图片路径或 http(s) URL（可重复传多张）")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help="多模态模型名（默认 %s）" % DEFAULT_MODEL)
    parser.add_argument("--session", help="视觉多轮会话 JSONL 文件（追问保留上下文）")
    parser.add_argument("--json", action="store_true", help="输出 SDK 兼容 JSON 形状")
    parser.add_argument("-o", "--output", help="把结果写入该路径")
    parser.add_argument("--timeout", type=int, default=TIMEOUT,
                        help="HTTP 超时秒数（默认 %d）" % TIMEOUT)
    args = parser.parse_args()
    try:
        return do_vision(args)
    except KeyboardInterrupt:
        eprint("[glmvlm] 已中断")
        return 1


if __name__ == "__main__":
    sys.exit(main())
