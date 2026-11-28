#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""glmllm.py — glm-llm Codex 插件的本地对话 CLI。

等效替换源 skill（skills/LLM）对 z-ai-web-dev-sdk `zai.chat.completions.create()`
与 `z-ai chat` CLI 的调用：本地不部署该 SDK，全部能力改经
Ollama 原生 /api/chat 端点完成（默认模型可用环境变量或 --model 参数覆盖）。

纯 Python 标准库，零 pip 依赖。

用法：
  glmllm.py chat -p "问题"                       # 单轮问答（stdout 纯文本）
  glmllm.py chat -p "..." -s "你是资深代码评审"  # system 提示
  glmllm.py chat -p "..." --think                # 开启思维链（需模型支持思考）
  glmllm.py chat -p "..." --stream               # 流式打印
  glmllm.py chat -p "..." --session s.jsonl      # 多轮会话（JSONL 历史追加）
  glmllm.py chat -p "..." --json -o out.json     # SDK 兼容 JSON 输出
退出码：0 成功 / 1 用法错误 / 2 网络或模型服务错误（stderr 报因，不假死）。
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_MODEL = os.environ.get("GLM_LLM_MODEL", "qwen3.8:27b")
DEFAULT_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
TIMEOUT = int(os.environ.get("GLM_LLM_TIMEOUT", "600"))


def eprint(msg):
    print(msg, file=sys.stderr)


def host_url(path):
    host = DEFAULT_HOST.rstrip("/")
    if not (host.startswith("http://") or host.startswith("https://")):
        host = "http://" + host
    return host + path


def post_chat(model, messages, stream=False, think=False, timeout=TIMEOUT):
    """调用 Ollama /api/chat，返回 (status, payload_or_stream)。"""
    body = {"model": model, "messages": messages, "stream": stream}
    if think:
        body["think"] = True
    req = urllib.request.Request(
        host_url("/api/chat"),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:400]
        except Exception:
            pass
        return ("http_error", "HTTP %s: %s" % (e.code, detail or e.reason))
    except (urllib.error.URLError, OSError, ValueError) as e:
        return ("net_error", "cannot reach Ollama at %s (%s)" % (host_url("/api/chat"), e))
    return ("ok", resp)


def sdk_shape(ok_payload, model):
    """把 Ollama 响应映射成源 SDK completion 的形状（choices[0].message.content）。"""
    msg = (ok_payload or {}).get("message", {}) or {}
    out = {
        "id": "glmllm-" + str(ok_payload.get("created_at", "")),
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": msg.get("content", "")},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": ok_payload.get("prompt_eval_count", 0),
            "completion_tokens": ok_payload.get("eval_count", 0),
            "total_tokens": ok_payload.get("prompt_eval_count", 0)
            + ok_payload.get("eval_count", 0),
        },
    }
    if ok_payload.get("thinking"):
        out["thinking"] = ok_payload.get("thinking")
    return out


def load_history(session_path):
    if not os.path.exists(session_path):
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
    with open(session_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"role": role, "content": content}, ensure_ascii=False) + "\n")


def read_prompt_from_stdin():
    if sys.stdin is None or sys.stdin.isatty():
        return None
    data = sys.stdin.read()
    return data if data.strip() else None


def do_chat(args):
    prompt = args.prompt
    if not prompt and args.stdin:
        prompt = read_prompt_from_stdin()
    if not prompt or not str(prompt).strip():
        eprint("用法错误：-p/--prompt 或 --stdin 必须提供用户消息")
        return 1

    messages = []
    if args.system and args.system.strip():
        messages.append({"role": "system", "content": args.system})
    if args.session:
        history = load_history(args.session)
        if history and history[0].get("role") == "system" and not args.system:
            messages = [history[0]]
            history = history[1:]
        elif args.system:
            messages = [{"role": "system", "content": args.system}]
        messages.extend(history)
    messages.append({"role": "user", "content": str(prompt)})

    last_err = None
    for attempt in range(1, max(1, args.retries) + 1):
        status, payload = post_chat(
            args.model, messages, stream=args.stream, think=args.think,
            timeout=args.timeout,
        )
        if status == "ok":
            if args.stream:
                text_parts = []
                thinking_parts = []
                try:
                    for raw in payload:
                        line = raw.decode("utf-8", "replace").strip()
                        if not line:
                            continue
                        chunk = json.loads(line)
                        m = chunk.get("message", {}) or {}
                        if m.get("thinking"):
                            thinking_parts.append(m["thinking"])
                        if m.get("content"):
                            text_parts.append(m["content"])
                            sys.stdout.write(m["content"])
                            sys.stdout.flush()
                        if chunk.get("done"):
                            break
                except (urllib.error.URLError, OSError) as e:
                    eprint("\n[glmllm] 流中断: %s" % e)
                    return 2
                sys.stdout.write("\n")
                if args.session:
                    append_history(args.session, "user", str(prompt))
                    append_history(args.session, "assistant", "".join(text_parts))
                if args.json:
                    out = {
                        "success": True,
                        "model": args.model,
                        "stream": True,
                        "choices": [{"message": {"role": "assistant",
                                                 "content": "".join(text_parts)}}],
                    }
                    if thinking_parts:
                        out["thinking"] = "".join(thinking_parts)
                    print(json.dumps(out, ensure_ascii=False, indent=2))
                return 0
            raw = payload.read().decode("utf-8", "replace")
            try:
                ok_payload = json.loads(raw)
            except ValueError:
                eprint("[glmllm] Ollama 返回非 JSON 响应（前 200 字）: %s" % raw[:200])
                return 2
            content = ((ok_payload.get("message") or {}).get("content")) or ""
            if args.session:
                append_history(args.session, "user", str(prompt))
                append_history(args.session, "assistant", content)
            if args.json:
                out = sdk_shape(ok_payload, args.model)
                out["success"] = True
                text = json.dumps(out, ensure_ascii=False, indent=2)
            else:
                text = content
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(text if args.json else json.dumps(
                        sdk_shape(ok_payload, args.model), ensure_ascii=False, indent=2))
                print("[glmllm] 已写入 %s" % args.output)
            else:
                print(text)
            return 0
        # 失败路径
        last_err = payload
        if status == "http_error" and "model not found" in str(payload).lower():
            eprint("[glmllm] 模型不存在：%s。先执行: ollama pull %s" % (args.model, args.model))
            return 2
        if attempt < args.retries:
            wait = attempt * 2
            eprint("[glmllm] 第 %d 次尝试失败（%s），%ds 后重试…" % (attempt, payload, wait))
            time.sleep(wait)
    eprint("[glmllm] 失败（已重试 %d 次）: %s" % (args.retries, last_err))
    eprint("[glmllm] 检查: ollama serve 是否运行 / OLLAMA_HOST 是否正确 / ollama list 是否含该模型")
    return 2


def main():
    parser = argparse.ArgumentParser(
        prog="glmllm.py", description="glm-llm：本地 Ollama 对话 CLI（z-ai chat 的等效替换）")
    sub = parser.add_subparsers(dest="cmd")

    chat = sub.add_parser("chat", help="单轮/多轮对话补全")
    chat.add_argument("-p", "--prompt", help="用户消息（或用 --stdin 从管道读）")
    chat.add_argument("--stdin", action="store_true", help="从 stdin 读取用户消息")
    chat.add_argument("-s", "--system", help="system 提示（默认无）")
    chat.add_argument("--model", default=DEFAULT_MODEL,
                      help="Ollama 模型名（默认 %s）" % DEFAULT_MODEL)
    chat.add_argument("--think", action="store_true",
                      help="开启思维链（think:true；需模型支持思考）")
    chat.add_argument("--stream", action="store_true", help="流式输出")
    chat.add_argument("--session", help="多轮会话 JSONL 文件（不存在则创建，逐轮追加）")
    chat.add_argument("--json", action="store_true", help="输出 SDK 兼容 JSON 形状")
    chat.add_argument("-o", "--output", help="把 JSON 结果写入该路径")
    chat.add_argument("--retries", type=int, default=2, help="网络错误重试次数（默认 2）")
    chat.add_argument("--timeout", type=int, default=TIMEOUT,
                      help="HTTP 超时秒数（默认 %d，本地大模型推理较慢请勿调小）" % TIMEOUT)
    chat.set_defaults(func=do_chat)

    args = parser.parse_args()
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    try:
        return args.func(args)
    except KeyboardInterrupt:
        eprint("[glmllm] 已中断")
        return 1


if __name__ == "__main__":
    sys.exit(main())
