#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""glmtts.py — glm-tts Codex 插件的本地文字转语音 CLI。

等效替换源 skill（skills/TTS）对 z-ai-web-dev-sdk `zai.audio.tts.create()`
与 `z-ai tts` CLI 的调用：本地不部署该 SDK，也无云端 TTS。等效链完全采用
macOS 自带工具（零安装）：

  say（系统语音合成）→ aiff → afconvert（转 wav 16bit/24kHz、m4a/aac）
  mp3 / pcm 输出需要 ffmpeg（可选，缺失时 exit 2 给指引）

纯 Python 标准库编排，零 pip 依赖。

用法：
  glmtts.py speak -i "你好，世界" -o ./hello.wav            # 默认 wav
  glmtts.py speak -i "…" -o out.m4a --voice jam             # 英音
  glmtts.py speak -i "…" -o out.wav --speed 1.5 --volume 2 # 加速+增益
  glmtts.py speak -i "长文本…" -o book.wav                  # 本地无 1024 限制
  glmtts.py voices                                          # 查看语音映射表
退出码：0 成功 / 1 用法错误 / 2 工具缺失或合成失败（stderr 报因，不假死）。
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

SPEED_BASE_WPM = 180  # speed 1.0 的基准语速（词/分钟）
SAMPLE_RATE = 24000   # 与源 skill 推荐采样率一致（24kHz）

# 源 SDK 7 音色 → macOS 系统语音（人格近似映射；--voice 也可直接传系统语音名）
VOICE_MAP = {
    "tongtong": ("Tingting", "zh-CN", "温暖亲切（中文女声）"),
    "chuichui": ("Meijia", "zh-TW", "活泼可爱（台湾国语女声）"),
    "xiaochen": ("Sinji", "zh-HK", "沉稳专业（粤语女声）"),
    "jam": ("Daniel", "en-GB", "英音绅士（英国男声）"),
    "kazi": ("Samantha", "en-US", "清晰标准（美国女声）"),
    "douji": ("Alex", "en-US", "自然流畅（美国男声）"),
    "luodo": ("Karen", "en-AU", "富有感染力（澳洲女声）"),
}


def eprint(msg):
    print(msg, file=sys.stderr)


def resolve_voice(name):
    """返回 (系统语音名, 说明) —— 映射键或直接系统语音名。"""
    if not name:
        return ("Tingting", "默认（tongtong 近似）")
    key = name.strip().lower()
    if key in VOICE_MAP:
        v = VOICE_MAP[key]
        return (v[0], "%s → %s（%s）" % (name, v[0], v[2]))
    return (name, "直接使用系统语音名（`say -v '?'` 可列出全部）")


def have_tool(name):
    return shutil.which(name) is not None


def speed_to_wpm(speed):
    try:
        s = float(speed)
    except (TypeError, ValueError):
        eprint("用法错误：--speed 需为 0.5–2.0 之间的数字")
        return None
    if s < 0.5 or s > 2.0:
        eprint("用法错误：--speed 超出 [0.5, 2.0]（源 API 约束沿用）：%.2f" % s)
        return None
    return max(90, min(400, round(SPEED_BASE_WPM * s)))


def run(cmd, timeout=600):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    except OSError as e:
        eprint("[glmtts] 无法运行 %s (%s)" % (cmd[0], e))
        return None


def do_speak(args):
    if not args.input or not str(args.input).strip():
        eprint("用法错误：-i/--input 必须提供文本（本地链无 1024 字符上限）")
        return 1
    if not args.output:
        eprint("用法错误：-o/--output 必须提供输出路径")
        return 1
    ext = os.path.splitext(args.output)[1].lower()
    fmt = args.format or {".wav": "wav", ".m4a": "m4a", ".aiff": "aiff",
                         ".mp3": "mp3", ".pcm": "pcm", ".aif": "aiff"}.get(ext, "wav")
    if args.format:
        fmt = args.format.lower()

    if not have_tool("say"):
        eprint("[glmtts] 未找到 say 命令 — 本插件 TTS 链为 macOS 设计"
               "（say + afconvert 系统自带）。Linux 等效可装 espeak-ng 后自行替换本链。")
        return 2

    wpm = speed_to_wpm(args.speed)
    if wpm is None:
        return 1
    try:
        vol = float(args.volume) if args.volume is not None else 1.0
    except (TypeError, ValueError):
        eprint("用法错误：--volume 需为数字（0 < v ≤ 10，沿源 API 约束）")
        return 1
    if not (0 < vol <= 10):
        eprint("用法错误：--volume 超出 (0, 10]（源 API 约束沿用）：%s" % vol)
        return 1

    voice, vdesc = resolve_voice(args.voice)

    tmpdir = tempfile.mkdtemp(prefix="glmtts_")
    aiff = os.path.join(tmpdir, "tts.aiff")
    text = str(args.input).strip()

    r = run(["say", "-o", aiff, "--voice", voice, "--rate", str(wpm), text])
    if r is None or r.returncode != 0 or not os.path.exists(aiff) or os.path.getsize(aiff) < 100:
        eprint("[glmtts] say 合成失败（语音名可能不存在：'say -v ?' 列出可用语音）：%s"
               % ((r.stderr if r else "")[:300]))
        return 2
    eprint("[glmtts] 语音 %s 语速 %dwpm（speed %.2f）" % (vdesc, wpm, float(args.speed or 1.0)))

    # 中间产物 aiff → 目标格式
    if fmt == "aiff":
        final = args.output
        shutil.copyfile(aiff, final)
    elif fmt == "wav":
        final = args.output
        if not have_tool("afconvert"):
            eprint("[glmtts] 未找到 afconvert（macOS 自带，请检查系统完整性）")
            return 2
        r = run(["afconvert", "-f", "WAVE", "-d", "LEI16@%d" % SAMPLE_RATE, "-c", "1", aiff, final])
        if r is None or r.returncode != 0:
            eprint("[glmtts] afconvert 转 wav 失败：%s" % ((r.stderr if r else "")[:300]))
            return 2
    elif fmt == "m4a":
        final = args.output
        if not have_tool("afconvert"):
            return (_missing_afconvert(), 2)[1]
        r = run(["afconvert", "-f", "m4af", "-d", "aac", aiff, final])
        if r is None or r.returncode != 0:
            eprint("[glmtts] afconvert 转 m4a 失败：%s" % ((r.stderr if r else "")[:300]))
            return 2
    elif fmt in ("mp3", "pcm"):
        final = args.output
        if not have_tool("ffmpeg"):
            eprint("[glmtts] %s 输出需要 ffmpeg（macOS: brew install ffmpeg）"
                   "——wav/m4a 走系统 afconvert 零依赖链" % fmt.upper())
            return 2
        if fmt == "mp3":
            r = run(["ffmpeg", "-y", "-i", aiff, "-codec:a", "libmp3lame",
                     "-b:a", "128k", "-ar", str(SAMPLE_RATE), final])
        else:
            r = run(["ffmpeg", "-y", "-i", aiff, "-f", "s16le",
                     "-ac", "1", "-ar", str(SAMPLE_RATE), final])
        if r is None or r.returncode != 0:
            eprint("[glmtts] ffmpeg 转换失败：%s" % ((r.stderr if r else "")[-300:]))
            return 2
    else:
        eprint("用法错误：不支持的格式 %s（wav/m4a/aiff/mp3/pcm）" % fmt)
        return 1

    # volume 增益（源 API 参数兼容）：afconvert/say 无对应能力，有 ffmpeg 时后处理
    if vol != 1.0:
        if have_tool("ffmpeg"):
            tmp_out = final + ".vol"
            r = run(["ffmpeg", "-y", "-i", final, "-af", "volume=%.2f" % vol, tmp_out])
            if r is not None and r.returncode == 0 and os.path.exists(tmp_out):
                os.replace(tmp_out, final)
                eprint("[glmtts] 音量增益 ×%.2f 已应用（ffmpeg 后处理）" % vol)
            else:
                eprint("[glmtts] NOTE: 音量增益失败（ffmpeg 报错），保留原始响度")
        else:
            eprint("[glmtts] NOTE: --volume 在本无 ffmpeg 环境不生效（say/afconvert 无增益能力），"
                   "输出保持原始响度；如需增益: brew install ffmpeg 后重跑")

    size = os.path.getsize(final)
    print("[glmtts] 已生成 %s（%s，%.1fKB，采样率 %dHz）"
          % (final, fmt.upper(), size / 1024.0, SAMPLE_RATE))
    shutil.rmtree(tmpdir, ignore_errors=True)
    return 0


def _missing_afconvert():
    eprint("[glmtts] 未找到 afconvert（macOS 自带，请检查系统完整性）")
    return 2


def do_voices(args):
    print("源 SDK 音色 → macOS 系统语音映射（--voice 可传左列键，或直接传系统语音名）：")
    for k, (v, lang, desc) in VOICE_MAP.items():
        print("  %-10s → %-10s [%s] %s" % (k, v, lang, desc))
    print("查看全部系统语音：say -v '?'（中文：Tingting/Meijia/Sinji；英文：Daniel/Samantha/Alex/Karen…）")
    print("提示：系统若未装某语音（设置 → 辅助功能 → 朗读内容 → 系统声音 → 管理语音…）可从该处下载。")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="glmtts.py",
        description="glm-tts：本地文字转语音 CLI（z-ai tts 的等效替换，macOS say 链）")
    sub = parser.add_subparsers(dest="cmd")

    s = sub.add_parser("speak", help="文本转语音并落盘")
    s.add_argument("-i", "--input", help="要合成的文本（本地链无 1024 字符上限）")
    s.add_argument("-o", "--output", help="输出音频路径（扩展名决定格式：wav/m4a/aiff/mp3/pcm）")
    s.add_argument("-v", "--voice", help="音色：源键名（tongtong/chuichui/xiaochen/jam/kazi/douji/luodo）或系统语音名")
    s.add_argument("-s", "--speed", default="1.0", help="语速 0.5–2.0（默认 1.0）")
    s.add_argument("--volume", help="音量 (0,10]（默认 1.0；需 ffmpeg 才实际生效）")
    s.add_argument("-f", "--format", help="强制格式 wav/m4a/aiff/mp3/pcm（默认按扩展名，缺省 wav）")
    s.set_defaults(func=do_speak)

    v = sub.add_parser("voices", help="列出音色映射表")
    v.set_defaults(func=do_voices)

    args = parser.parse_args()
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    try:
        return args.func(args)
    except KeyboardInterrupt:
        eprint("[glmtts] 已中断")
        return 1


if __name__ == "__main__":
    sys.exit(main())
