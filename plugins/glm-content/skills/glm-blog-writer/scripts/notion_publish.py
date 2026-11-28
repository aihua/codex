#!/usr/bin/env python3
"""glm-blog-writer 的 Notion 发布脚本：等效替换源 skill 的宿主 Notion MCP 集成。
纯 Python 标准库（urllib），无 SDK 依赖。

用法:
  python3 notion_publish.py <post.md> [--title "标题"] [--save-local DIR] [--dry-run]

环境:
  NOTION_TOKEN — https://www.notion.so/my-integrations 创建 integration 后获得
  （需对该 integration 授权目标数据库所在页面）。

目标（沿源 skill 的发布契约）:
  数据库 "TS Notes" data source ID 04a872be-8bed-4f43-a448-3dfeebc0df21
  属性: Note = 标题; Type = "Writing"; Project(s) = My Writing 项目
        （页面 ID 2a5b4629-bb37-8018-9199-f3c496980c0c）
  正文: Markdown → Notion 块（headings/quote/lists/divider/code/image/段落，
        行内 **bold**/*italic*/`code`/[link](url) 富文本注解）。

退出码: 0 发布成功（stdout 打印页面 URL）
        1 用法/文件错误
        2 NOTION_TOKEN 未设置（stderr 打印引导）
        3 Notion API 错误（stderr 打印响应体）
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
DATA_SOURCE_ID = "04a872be-8bed-4f43-a448-3dfeebc0df21"
PROJECT_PAGE_ID = "2a5b4629-bb37-8018-9199-f3c496980c0c"
MAX_CHILDREN = 100


# ---------------- Markdown → Notion 块 ----------------

def rich_text(segment: str) -> list:
    """把一段行内文本解析为 Notion rich_text 数组（bold/italic/code/link）。"""
    out = []
    pattern = re.compile(
        r"(\*\*(?P<bold>.+?)\*\*)"          # **bold**
        r"|(`(?P<code>[^`]+)`)"              # `code`
        r"|(\[(?P<ltext>[^\]]+)\]\((?P<lurl>[^)\s]+)\))"  # [text](url)
        r"|(?<!\*)(\*(?P<italic>[^*]+)\*)(?!\*)"           # *italic*
    )
    pos = 0
    for m in pattern.finditer(segment):
        if m.start() > pos:
            out.append({"type": "text", "text": {"content": segment[pos:m.start()]}})
        if m.group("bold") is not None:
            out.append({"type": "text", "text": {"content": m.group("bold")},
                        "annotations": {"bold": True}})
        elif m.group("code") is not None:
            out.append({"type": "text", "text": {"content": m.group("code")},
                        "annotations": {"code": True}})
        elif m.group("ltext") is not None:
            out.append({"type": "text",
                        "text": {"content": m.group("ltext"),
                                 "link": {"url": m.group("lurl")}}})
        elif m.group("italic") is not None:
            out.append({"type": "text", "text": {"content": m.group("italic")},
                        "annotations": {"italic": True}})
        pos = m.end()
    if pos < len(segment):
        out.append({"type": "text", "text": {"content": segment[pos:]}})
    return out or [{"type": "text", "text": {"content": segment}}]


def md_to_blocks(md_text: str) -> list:
    """Markdown → Notion 块序列（代码块/标题/引用/列表/分割线/图片/段落）。"""
    blocks, lines, i = [], md_text.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            lang = line[3:].strip() or "plain text"
            body, i = [], i + 1
            while i < len(lines) and not lines[i].startswith("```"):
                body.append(lines[i]); i += 1
            i += 1
            blocks.append({"object": "block", "type": "code",
                           "code": {"rich_text": [{"type": "text",
                                "text": {"content": "\n".join(body)}}],
                                "language": lang}})
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            blocks.append({"object": "block", "type": "heading_%d" % lvl,
                           "heading_%d" % lvl: {"rich_text": rich_text(m.group(2))}})
        elif re.match(r"^(-{3,}|\*{3,})\s*$", line):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        elif line.startswith("> "):
            blocks.append({"object": "block", "type": "quote",
                           "quote": {"rich_text": rich_text(line[2:])}})
        elif re.match(r"^\s*[-*]\s+", line):
            blocks.append({"object": "block", "type": "bulleted_list_item",
                           "bulleted_list_item": {"rich_text":
                               rich_text(re.sub(r"^\s*[-*]\s+", "", line))}})
        elif re.match(r"^\s*\d+[.)]\s+", line):
            blocks.append({"object": "block", "type": "numbered_list_item",
                           "numbered_list_item": {"rich_text":
                               rich_text(re.sub(r"^\s*\d+[.)]\s+", "", line))}})
        else:
            m = re.match(r"^!\[(.*?)\]\((.+?)\)\s*$", line)
            if m and m.group(2).startswith("http"):
                blocks.append({"object": "block", "type": "image",
                               "image": {"type": "external",
                                         "external": {"url": m.group(2)}}})
            elif line.strip():
                blocks.append({"object": "block", "type": "paragraph",
                               "paragraph": {"rich_text": rich_text(line)}})
        i += 1
    return blocks


def post_payload(title: str, md_text: str) -> dict:
    return {
        "parent": {"type": "database_id", "database_id": DATA_SOURCE_ID},
        "properties": {
            "Note": {"title": [{"text": {"content": title}}]},
            "Type": {"select": {"name": "Writing"}},
            "Project(s)": {"relation": [{"id": PROJECT_PAGE_ID}]},
        },
        "children": md_to_blocks(md_text)[:MAX_CHILDREN],
    }


def notion_request(method: str, path: str, token: str, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        NOTION_API + path, data=data, method=method,
        headers={"Authorization": "Bearer " + token,
                 "Notion-Version": NOTION_VERSION,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def publish(md_path: pathlib.Path, title, dry_run: bool, token, local=None):
    md_text = md_path.read_text(encoding="utf-8")
    if not title:
        title = next((l.lstrip("# ").strip() for l in md_text.splitlines()
                      if l.startswith("# ")), md_path.stem)
    payload = post_payload(title, md_text)
    if dry_run:
        print(json.dumps({"mode": "dry-run", "title": title,
                          "blocks": len(payload["children"]),
                          "data_source_id": DATA_SOURCE_ID},
                         ensure_ascii=False, indent=2))
        return None
    if not token:
        where = " also saved locally to %s" % local if local else ""
        print("NOTION_TOKEN is not set. Create an integration at "
              "https://www.notion.so/my-integrations, grant it access to the "
              "TS Notes database, then: export NOTION_TOKEN=secret_... "
              "(the post was%s)" % where,
              file=sys.stderr)
        sys.exit(2)
    try:
        page = notion_request("POST", "/pages", token, payload)
    except urllib.error.HTTPError as e:
        print("Notion API error %s:\n%s" % (e.code, e.read().decode("utf-8", "replace")),
              file=sys.stderr)
        sys.exit(3)
    # 超过 100 块的部分按批追加
    extra = md_to_blocks(md_text)[MAX_CHILDREN:]
    while extra:
        batch, extra = extra[:MAX_CHILDREN], extra[MAX_CHILDREN:]
        try:
            notion_request("PATCH", "/blocks/%s/children" % page["id"],
                           token, {"children": batch})
        except urllib.error.HTTPError:
            print("append failed; page created, blocks partially appended",
                  file=sys.stderr)
            break
    return page


def save_local(md_path: pathlib.Path, out_dir: pathlib.Path) -> pathlib.Path:
    today = datetime.date.today().isoformat()
    slug = re.sub(r"[^a-z0-9]+", "-", md_path.stem.lower()).strip("-")[:60] or "post"
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / ("%s-%s.md" % (today, slug))
    dst.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    return dst


def main() -> None:
    ap = argparse.ArgumentParser(description="Publish a Markdown post to the TS Notes Notion database.")
    ap.add_argument("post", help="path to the .md post")
    ap.add_argument("--title", help="override the page title (defaults to the post's # heading)")
    ap.add_argument("--save-local", metavar="DIR", default="output/blog-writer",
                    help="also save a dated copy locally (default output/blog-writer)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the payload summary without sending")
    args = ap.parse_args()
    md_path = pathlib.Path(args.post)
    if not md_path.is_file() or md_path.suffix.lower() != ".md":
        print("usage error: %s must be an existing .md file" % args.post, file=sys.stderr)
        sys.exit(1)
    token = os.environ.get("NOTION_TOKEN")
    # 本地兑底先行：非 dry-run 一律先存带日期副本，发布失败/缺 token 时内容不丢
    local = None if args.dry_run else save_local(md_path, pathlib.Path(args.save_local))
    page = publish(md_path, args.title, args.dry_run, token, local)
    if page:
        print(page.get("url") or ("page id: " + str(page.get("id"))))
    if local:
        print("local copy: %s" % local)


if __name__ == "__main__":
    main()
