#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""glmasr.py — glm-asr Codex 插件的本地语音转文字 CLI。

等效替换源 skill（skills/ASR）对 z-ai-web-dev-sdk `zai.audio.asr.create()`
与 `z-ai asr` CLI 的调用：本地不部署该 SDK，也无云端 ASR。等效后端链：

  1) faster-whisper（经 `uv run --with faster-whisper` 即用即建临时环境，
     用户已用 uv 管理 Python 依赖；支持 wav/mp3/m4a/flac/ogg，中文可用
     small 及以上档；模型首次自动从 HuggingFace 下载，可用 HF_ENDPOINT
     镜像加速）
  2) whisper-cli（whisper.cpp，`brew install whisper-cpp`；仅吃 16kHz wav）

两者都没有时 exit 2 并给出安装指引。本脚本自身纯 Python 标准库、零 pip 依赖。

用法：
  glmasr.py transcribe -f ./audio.mp3                  # 转写（stdout 纯文本）
  glmasr.py transcribe -f a.wav --model small          # 中文建议 small+
  glmasr.py transcribe -f a.wav --lang zh              # 跳过语言检测
  glmasr.py transcribe -f a.wav --json -o out.json     # SDK 兼容 JSON
  glmasr.py transcribe --base64 "UklGRiQ..."           # base64 输入兼容源 CLI
退出码：0 成功 / 1 用法错误 / 2 后端缺失或转写失败（stderr 报因，不假死）。
"""
import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile

DEFAULT_MODEL = os.environ.get("GLM_ASR_MODEL", "small")
TIMEOUT = int(os.environ.get("GLM_ASR_TIMEOUT", "1800"))

WORKER = r'''
import json, sys
_a = sys.argv[1:]
if _a and _a[0] == "--": _a = _a[1:]
path, model_id, lang = _a[0], _a[1], (_a[2] if len(_a) > 2 and _a[2] else None)
from faster_whisper import WhisperModel
try:
    m = WhisperModel(model_id, device="cpu", compute_type="int8")
    segments, info = m.transcribe(path, language=lang, vad_filter=True)
    text = "".join(s.text.strip() + " " for s in segments).strip()
    print(json.dumps({"text": text, "language": info.language,
                      "duration": round(info.duration or 0.0, 2)}, ensure_ascii=False))
except Exception as e:
    print(json.dumps({"err": str(e)}, ensure_ascii=False))
    sys.exit(0)
'''


def eprint(msg):
    print(msg, file=sys.stderr)


def sniff_ext(b64):
    head = base64.b64decode(b64[:16] + "==")
    if head.startswith(b"\x1f\x8b"):
        return ".flac.gz"
    if head.startswith(b"ID3") or head.startswith(b"\xff\xfb"):
        return ".mp3"
    if head.startswith(b"OggS"):
        return ".ogg"
    if head.startswith(b"fLaC"):
        return ".flac"
    return ".wav"


def find_backend():
    uv = shutil.which("uv")
    if uv:
        return ("uv-faster-whisper", uv)
    wcli = shutil.which("whisper-cli")
    if wcli:
        return ("whisper-cli", wcli)
    return (None, None)


def transcribe_with_uv(uv, path, model, lang):
    cmd = [uv, "run", "--quiet", "--with", "faster-whisper",
           "python", "-c", WORKER, "--", path, model, lang or ""]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=TIMEOUT, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    except subprocess.TimeoutExpired:
        return (None, "转写超时（>%ds）；音频过长或档位过高，换 --model base 或切短分段" % TIMEOUT)
    except OSError as e:
        return (None, "无法运行 uv (%s)" % e)
    if r.returncode != 0:
        return (None, "uv/faster-whisper 运行失败：%s" % (r.stderr or r.stdout)[-500:])
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if "err" in d:
            return (None, "faster-whisper 报错：%s（检查模型名与磁盘空间）" % d["err"])
        return (d, None)
    return (None, "uv 运行无有效输出：%s" % (r.stderr or r.stdout)[-300:])


def transcribe_with_whisper_cli(wcli, path, model):
    ggml = os.environ.get("GLM_ASR_GGML", "")
    candidates = [ggml] if ggml else []
    for base in ("/opt/whisper.cpp/models", "/usr/local/share/whisper.cpp/models",
                 os.path.expanduser("~/.cache/whisper"), os.path.expanduser("~/models")):
        candidates.append(os.path.join(base, "ggml-%s.bin" % model))
    model_path = next((c for c in candidates if c and os.path.exists(c)), None)
    if not model_path:
        return (None, "未找到 ggml-%s.bin（whisper.cpp 模型）。设 GLM_ASR_GGML 指向 "
                       "ggml 模型文件，或改用 uv faster-whisper 后端（安装 uv 即可）" % model)
    try:
        r = subprocess.run([wcli, "-m", model_path, "-f", path, "-otxt", "-of", "-"],
                           capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return (None, "转写超时（>%ds）" % TIMEOUT)
    except OSError as e:
        return (None, "无法运行 whisper-cli (%s)" % e)
    if r.returncode != 0:
        return (None, "whisper-cli 失败：%s" % (r.stderr or "")[-400:])
    text = (r.stdout or "").strip()
    return ({"text": text, "language": None, "duration": None}, None)


def do_transcribe(args):
    tmp_path = None
    path = args.file
    if not path and args.base64:
        try:
            data = base64.b64decode(args.base64)
        except Exception as e:
            eprint("用法错误：--base64 解码失败 (%s)" % e)
            return 1
        tmp_path = tempfile.NamedTemporaryFile(prefix="glmasr_", suffix=sniff_ext(args.base64),
                                                delete=False)
        tmp_path.write(data)
        tmp_path.close()
        path = tmp_path.name
    if not path:
        eprint("用法错误：-f/--file 或 --base64 必须提供音频")
        return 1
    if not os.path.exists(path):
        eprint("用法错误：文件不存在 %s" % path)
        return 1
    if os.path.getsize(path) > 400 * 1024 * 1024:
        eprint("[glmasr] 音频过大（>400MB），先切分再转写")
        return 2

    backend, tool = find_backend()
    try:
        if backend == "uv-faster-whisper":
            result, err = transcribe_with_uv(tool, path, args.model, args.lang)
        elif backend == "whisper-cli":
            eprint("[glmasr] 注意：whisper-cli 后端需要 16kHz wav；非该格式建议安装 uv 用主链")
            result, err = transcribe_with_whisper_cli(tool, path, args.model)
        else:
            eprint("[glmasr] 无可用本地 ASR 后端。二选一：")
            eprint("  1) 安装 uv（推荐，已有则检查 PATH）：brew install uv -- 或 -- uv 官方脚本")
            eprint("     之后无需预装任何包：本脚本经 uv run --with faster-whisper 即用即建")
            eprint("  2) 安装 whisper.cpp：brew install whisper-cpp 并下载 ggml 模型")
            return 2
        if result is None:
            eprint("[glmasr] 转写失败：%s" % err)
            eprint("[glmasr] 提示：中文识别建议 --model small 起步；首次运行会下载模型"
                   "（国内可 export HF_ENDPOINT=https://hf-mirror.com）")
            return 2
        text = result.get("text", "")
        if not text.strip():
            eprint("[glmasr] 转写结果为空：检查音频是否含清晰语音、音量与语言设置")
            return 2
        out = {
            "success": True,
            "text": text,
            "language": result.get("language"),
            "duration": result.get("duration"),
            "backend": backend,
            "model": args.model,
        }
        if args.json:
            payload = json.dumps(out, ensure_ascii=False, indent=2)
        else:
            payload = text
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(payload)
            print("[glmasr] 已写入 %s" % args.output)
        else:
            print(payload)
        return 0
    finally:
        if tmp_path and os.path.exists(tmp_path.name):
            os.unlink(tmp_path.name)


def main():
    parser = argparse.ArgumentParser(
        prog="glmasr.py",
        description="glm-asr：本地语音转文字 CLI（z-ai asr 的等效替换）")
    sub = parser.add_subparsers(dest="cmd")

    t = sub.add_parser("transcribe", help="转写音频文件")
    t.add_argument("-f", "--file", help="音频文件路径（wav/mp3/m4a/flac/ogg）")
    t.add_argument("-b", "--base64", help="base64 编码音频（兼容源 CLI 参数）")
    t.add_argument("--model", default=DEFAULT_MODEL,
                  help="whisper 模型档（tiny/base/small/medium/large-v3；默认 %s，中文建议 small 起）" % DEFAULT_MODEL)
    t.add_argument("--lang", help="强制语言（zh/en…；缺省自动检测）")
    t.add_argument("--json", action="store_true", help="输出 JSON（含 language/duration/backend）")
    t.add_argument("-o", "--output", help="把结果写入该路径")
    t.set_defaults(func=do_transcribe)

    args = parser.parse_args()
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    try:
        return args.func(args)
    except KeyboardInterrupt:
        eprint("[glmasr] 已中断")
        return 1


if __name__ == "__main__":
    sys.exit(main())
