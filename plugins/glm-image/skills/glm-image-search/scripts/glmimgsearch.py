#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""glmimgsearch.py — glm-image-search Codex 插件的本地图片检索 CLI。

等效替换源 skill（skills/image-search）对 `z-ai image-search` CLI
（ZAI 自家图片搜索服务：检索 + OSS 转存 + 配图说明）的调用：本地不部署
该 SDK 与服务。等效为 **Bing Images HTML 检索**（零 key、纯标准库）：

  https://www.bing.com/images/search?q=<query> 中的 iusc 结果卡自带原图
  直链（m 属性 JSON 的 murl 字段），提取后按源 schema 输出：
  { success, query, count, ranked, results:[{ original_url, caption,
  source, original_width, original_height }] }。

  与源服务的差异（诚实声明）：无 OSS 转存——返回的是源站原图直链，
  可达性以源站为准（重要素材建议随即落盘保存）。

用法：
  glmimgsearch.py -q "a cute orange tabby kitten" --count 5
  glmimgsearch.py -q "中国传统水墨山水画" --gl cn -o results.json
  glmimgsearch.py -q "vintage red sports car" --gl us --no-rank
退出码：0 成功 / 1 用法错误 / 2 网络失败或零结果（stderr 报因，不假死）。
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

GL_MAP = {"cn": ("zh-CN", "zh-hans"), "us": ("en-US", "en"),
          "jp": ("ja-JP", "ja"), "kr": ("ko-KR", "ko")}
TIMEOUT = int(os.environ.get("GLM_IMGSEARCH_TIMEOUT", "30"))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def eprint(msg):
    print(msg, file=sys.stderr)


def fetch_bing_images(query, count, gl):
    """抓 Bing Images 结果页并解析 iusc 卡的 m 属性 JSON。"""
    mkt, setlang = GL_MAP.get(gl, GL_MAP["cn"])
    params = urllib.parse.urlencode({
        "q": query, "form": "HDRSC2", "first": "1",
        "count": str(max(35, count * 2)), "mkt": mkt, "setlang": setlang,
    })
    url = "https://www.bing.com/images/search?" + params
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Language": "%s;q=0.8,en;q=0.5" % setlang,
        "Accept": "text/html,application/xhtml+xml",
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            page = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return (None, "Bing 返回 HTTP %s（可能被风控；稍后重试或换 --gl）" % e.code)
    except (urllib.error.URLError, OSError) as e:
        return (None, "无法访问 Bing（%s）——检查网络/代理；大陆网络通常可达" % e)

    # iusc 结果卡：<a class="iusc" ... m="{&quot;murl&quot;:…}">
    items = []
    for m in re.finditer(r'class="iusc"[^>]*?\sm="([^"]+)"', page):
        raw = html.unescape(m.group(1))
        try:
            d = json.loads(raw)
        except ValueError:
            continue
        murl = d.get("murl") or ""
        if not murl.startswith("http"):
            continue
        p = str(d.get("p") or "")
        w = h = ""
        if "x" in p:
            w, h = (v + "px" for v in p.split("x", 1))
        items.append({
            "original_url": murl,
            "caption": str(d.get("t") or "").strip(),
            "source": urllib.parse.urlsplit(murl).netloc,
            "original_width": w,
            "original_height": h,
        })
        if len(items) >= count:
            break
    return (items, None)


def do_search(args):
    if not args.query or not str(args.query).strip():
        eprint("用法错误：-q/--query 必须提供自然语言查询（描述句优于关键词堆砌）")
        return 1
    try:
        count = int(args.count)
    except (TypeError, ValueError):
        eprint("用法错误：--count 需数字（1–20）")
        return 1
    if not 1 <= count <= 20:
        eprint("用法错误：--count 需在 1–20（源服务约束沿用）")
        return 1
    gl = (args.gl or "cn").lower()
    if gl not in GL_MAP:
        eprint("用法错误：--gl 需为 cn/us/jp/kr")
        return 1

    query = str(args.query).strip()
    items, err = fetch_bing_images(query, count, gl)
    if items is None:
        eprint("[glmimgsearch] 检索失败：%s" % err)
        return 2
    if not items:
        eprint("[glmimgsearch] 零结果：放宽查询词 / 换语言重写 / 调大 --count / 换 --gl")
        return 2
    if args.no_rank:
        for it in items:
            it["caption"] = ""
    out = {
        "success": True,
        "query": query,
        "count": len(items),
        "ranked": not args.no_rank,
        "results": items,
        "note": "本地等效版无 OSS 转存：original_url 为源站直链，"
                "重要素材请随即保存到本地（可用同插件技能 glm-image-edit 处理）",
    }
    text = json.dumps(out, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print("[glmimgsearch] 已写入 %s（%d 张）" % (args.output, len(items)))
    else:
        print(text)
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="glmimgsearch.py",
        description="glm-image-search：本地 Bing 图片检索 CLI（z-ai image-search 的等效替换）")
    parser.add_argument("-q", "--query", help="自然语言查询句（中英皆可）")
    parser.add_argument("-c", "--count", default="5", help="数量 1–20（默认 5，沿源默认）")
    parser.add_argument("--gl", default="cn", choices=list(GL_MAP),
                         help="区域（默认 cn；captions 语言随区域）")
    parser.add_argument("--no-rank", action="store_true",
                        help="去掉 caption（源 CLI 同名旗标，加速等效）")
    parser.add_argument("-o", "--output", help="把 JSON 写入该路径")
    args = parser.parse_args()
    try:
        return do_search(args)
    except KeyboardInterrupt:
        eprint("[glmimgsearch] 已中断")
        return 1


if __name__ == "__main__":
    sys.exit(main())
