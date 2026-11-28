#!/usr/bin/env python3
"""glmwr - zero-dependency web page reader CLI for the glm-web-reader skill.

Local equivalent of the former cloud-SDK page_reader function: no SDK, no
API key, no third-party packages. Everything is parsed with the Python
standard library only (urllib.request + html.parser).

Subcommands:

    read URL     extract one page: title, description, author, publication
                 time, plain text, simplified article HTML, link count.
                 Auto-detects RSS/Atom feeds and JSON/plain-text endpoints.
    links URL    list hyperlinks found on the page (absolute, deduped).
    diagnose    layered connectivity report: DNS -> TCP -> HTTPS -> read.

Output schema of `read --json` is field-compatible with the original SDK
PageReaderFunctionResult (url, title, html, text, publishedTime, usage).
`usage.tokens` is reported as 0 because extraction is local: nothing is
metered, nothing leaves the machine except the page fetch itself.

Exit codes:
    0  success (page read, or >=1 link listed)
    1  fetched but nothing extractable (HTTP 4xx/5xx, JS-only page, or
       zero links) - not a network failure
    2  network/usage error (unreachable host, DNS, timeout, bad arguments)

On exit 2 the CLI prints layered hints on stderr that separate the common
causes (Codex command sandbox vs proxy vs firewall). `glmwr.py diagnose`
prints the full layer-by-layer report.
"""

import argparse
import concurrent.futures
import html as html_mod
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

VERSION = "1.0.0"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
               "*/*;q=0.8"),
    "Accept-Encoding": "identity",  # keep plain HTTP: no gzip to decode
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}
MAX_BYTES = 2_000_000          # hard cap on one page
BOILER_RE = re.compile(
    r"(nav|menu|sidebar|comment|share|social|related|recommend|banner|"
    r"advert|ad-|ads?|promo|breadcrumb|pagination|copyright|disclaimer|"
    r"subscribe|newsletter|widget|modal|cookie|consent|footer|topbar|"
    r"toolbar|skip-?link)", re.I)

# ---------------------------------------------------------------------------
# Fetch layer
# ---------------------------------------------------------------------------

def fetch(url, timeout=12):
    """GET a URL. Return (final_url, status, headers, raw_bytes).

    Raises urllib.error.URLError or OSError on network failure; HTTPError
    is returned as a normal (status >= 400) result with whatever body the
    server sent (possibly empty).
    """
    req = urllib.request.Request(url, headers=dict(HEADERS))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return (resp.geturl(), resp.status, resp.headers,
                    resp.read(MAX_BYTES))
    except urllib.error.HTTPError as e:
        try:
            body = e.read(MAX_BYTES)
        except Exception:
            body = b""
        return (url, e.code, e.headers or {}, body)


def decode_body(raw, header_charset):
    """Decode bytes: given charset, else <meta charset> sniff, else utf-8."""
    if header_charset:
        try:
            return raw.decode(header_charset, errors="replace")
        except (LookupError, UnicodeError):
            pass
    head = raw[:2048].decode("ascii", errors="ignore")
    m = (re.search(r'<meta[^>]+charset=["\']?([\w-]+)', head, re.I) or
         re.search(r'charset=([\w-]+)', head, re.I))
    if m:
        try:
            return raw.decode(m.group(1), errors="replace")
        except (LookupError, UnicodeError):
            pass
    return raw.decode("utf-8", errors="replace")


def normalize_url(url):
    url = (url or "").strip()
    if not url:
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if re.match(r"^[\w.-]+\.[a-z]{2,}([/:?#].*)?$", url, re.I):
        return "https://" + url
    return url


# ---------------------------------------------------------------------------
# Network diagnosis (why did the page fetch fail?)
# ---------------------------------------------------------------------------

_DNS_HOST = "www.bing.com"
_PROBE_URL = "https://" + _DNS_HOST + "/"
_PROXY_ENV_VARS = ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY",
                   "https_proxy", "http_proxy", "all_proxy")
_SANDBOX_HINTS = (
    "DNS resolution fails in this shell. If %s opens in your browser or "
    "your own terminal, the likely cause is the Codex command sandbox "
    "(macOS Seatbelt / Linux Landlock): it denies network to tool "
    "commands by default, while Codex's own model traffic is unaffected."
    % _DNS_HOST,
    'Fix: in ~/.codex/config.toml set  sandbox_mode = "workspace-write"  '
    'and add  [sandbox_workspace_write]  with  network_access = true , '
    'then restart Codex; or start codex with --sandbox danger-full-access.',
)


def _proxy_env():
    return {k: os.environ[k] for k in _PROXY_ENV_VARS if os.environ.get(k)}


def _dns_lookup(host=_DNS_HOST, timeout=6):
    """Resolve host in a worker thread so the call stays time-bounded."""
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        fut = executor.submit(socket.getaddrinfo, host, 443, 0,
                               socket.SOCK_STREAM)
        res = fut.result(timeout=timeout)
        return res[0][4][0], None
    except concurrent.futures.TimeoutError:
        return None, "name resolution timed out after %ss" % timeout
    except Exception as e:
        return None, "name resolution failed (%s)" % (e,)
    finally:
        try:
            executor.shutdown(wait=False, cancel_futures=True)
        except TypeError:  # Python < 3.9
            executor.shutdown(wait=False)


def _failure_hints(dns_ip, dns_err):
    """Actionable hints for the exit-2 path, based on a cheap DNS probe."""
    if not dns_err:
        return ["DNS works (%s -> %s) but the page host was unreachable: "
                "a TCP/TLS-level block (firewall, proxy ports) or the site "
                "itself is down. Run: glmwr.py diagnose" % (_DNS_HOST, dns_ip)]
    proxies = _proxy_env()
    if proxies:
        return ["DNS fails and a proxy is configured (%s). If that proxy "
                "is unreachable from this shell, every lookup breaks; "
                "fix or unset the proxy variables."
                % ", ".join(sorted(proxies))]
    return list(_SANDBOX_HINTS)


# ---------------------------------------------------------------------------
# Head parser: title / description / author / publishedTime / lang / JSON-LD
# ---------------------------------------------------------------------------

_SKIP_TAGS = {"script", "style", "noscript", "template", "svg", "head",
              "form", "select", "button", "iframe", "canvas", "object",
              "embed"}
_BLOCK_TAGS = {"p", "div", "li", "ul", "ol", "blockquote", "pre", "h1",
               "h2", "h3", "h4", "h5", "h6", "br", "tr", "section",
               "article", "figure", "figcaption", "dd", "dt", "dl",
               "table", "header", "main", "td", "th"}
_PUB_KEYS = ("article:published_time", "article:modified_time",
             "og:updated_time", "og:article:published_time", "pubdate",
             "publishdate", "publication_date", "datepublished",
             "date", "dc.date", "dc.date.issued", "revised")
_AUTHOR_KEYS = ("author", "article:author", "dc.creator", "byline",
                "twitter:creator", "sailthru.author")


class _HeadParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.published = ""
        self.author = ""
        self.lang = ""
        self.canonical = ""
        self.site_name = ""
        self.ld_json = []
        self.time_attrs = []
        self._in_title = False
        self._buf = []
        self._ld_buf = None
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in _SKIP_TAGS and tag != "head":   # title/meta live in head
            self._skip += 1
            if tag == "script" and (d.get("type") or "").lower() == \
                    "application/ld+json":
                self._ld_buf = []
            return
        if self._skip:
            return
        if tag == "title":
            self._in_title = True
            self._buf = []
        elif tag == "meta":
            name = (d.get("property") or d.get("name") or
                    d.get("itemprop") or "").lower()
            content = (d.get("content") or "").strip()
            if not content:
                return
            if name in ("description", "og:description",
                        "twitter:description") and not self.description:
                self.description = re.sub(r"\s+", " ", content)
            elif name in _PUB_KEYS and not self.published:
                if self._looks_date(content):
                    self.published = content
            elif name in ("og:title", "twitter:title") and not self.title:
                self.title = re.sub(r"\s+", " ", content)
            elif name in _AUTHOR_KEYS and not self.author and \
                    not content.lower().startswith(("http", "/")):
                self.author = re.sub(r"\s+", " ", content)
            elif name == "og:site_name" and not self.site_name:
                self.site_name = re.sub(r"\s+", " ", content)
        elif tag == "link":
            if (d.get("rel") or "").lower() == "canonical" and d.get("href"):
                self.canonical = d["href"].strip()
        elif tag == "time":
            dt = (d.get("datetime") or d.get("content") or "").strip()
            if dt and self._looks_date(dt) and len(self.time_attrs) < 5:
                self.time_attrs.append(dt)
        elif tag == "html" and d.get("lang"):
            self.lang = d["lang"].strip()

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and tag != "head":
            if self._skip:
                self._skip -= 1
            if tag == "script" and self._ld_buf is not None:
                self.ld_json.append("".join(self._ld_buf))
                self._ld_buf = None
        elif tag == "title":
            self._in_title = False
            if self._buf is not None and not self.title:
                self.title = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            self._buf = None

    def handle_data(self, data):
        if self._in_title and self._buf is not None:
            self._buf.append(data)
        elif self._ld_buf is not None:
            self._ld_buf.append(data)

    @staticmethod
    def _looks_date(s):
        return bool(re.match(r"^\d{4}-\d{2}(-\d{2})?([T ]\d{2})?", s) or
                    re.match(r"^\d{4}/\d{2}/\d{2}", s) or
                    re.match(r"^[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\b", s))


def _ld_facts(ld_texts):
    """Pull datePublished/author/headline from JSON-LD blocks (best effort)."""
    out = {"published": "", "modified": "", "author": "", "headline": ""}
    for txt in ld_texts:
        try:
            data = json.loads(txt)
        except Exception:
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                for key, field in (("datePublished", "published"),
                                   ("dateModified", "modified"),
                                   ("headline", "headline")):
                    val = node.get(key)
                    if isinstance(val, str) and not out[field]:
                        out[field] = val.strip()
                auth = node.get("author")
                if isinstance(auth, str) and not out["author"]:
                    out["author"] = auth.strip()
                elif isinstance(auth, list) and auth and \
                        not out["author"]:
                    first = auth[0]
                    if isinstance(first, str):
                        out["author"] = first.strip()
                    elif isinstance(first, dict) and \
                            isinstance(first.get("name"), str):
                        out["author"] = first["name"].strip()
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    return out


# ---------------------------------------------------------------------------
# Content parser: paragraphs, headings, links - boilerplate removed
# ---------------------------------------------------------------------------

class _ContentParser(HTMLParser):
    """One pass: text chunks (kind, text) + links (href, text, rel).

    `has_main_region` gates capture to <article>/<main>/[role=main] when
    the page has any of them, so navigation chrome outside is dropped.
    """

    def __init__(self, has_main_region):
        super().__init__(convert_charrefs=True)
        self.chunks = []          # [(kind, text)] kind: p/li/h1..h6/quote
        self.links = []            # [(href, text, rel)]
        self.has_main = has_main_region
        self._region = 0           # article/main nesting depth
        self._skip = 0             # skip-tags depth
        self._boiler = 0           # boilerplate-subtree depth
        self._buf = []
        self._kind = "p"
        self._anchor = None        # [href, rel, texts]

    @staticmethod
    def _boilerp(attrs):
        d = dict(attrs)
        token = " ".join(filter(None, [d.get("class"), d.get("id"),
                                        d.get("aria-label")]))
        return bool(token) and bool(BOILER_RE.search(token))

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in _SKIP_TAGS or tag == "head":
            self._skip += 1
            return
        if self._skip:
            return
        if tag in ("article", "main") or (
                tag == "div" and (d.get("role") or "").lower() == "main"):
            self._region += 1
        if self._boilerp(attrs):
            self._boiler += 1
            return
        if self._in_main_body():
            if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                self._flush()
                self._kind = tag
            elif tag == "blockquote":
                self._flush()
                self._kind = "quote"
            elif tag == "li":
                self._flush()
                self._kind = "li"
            elif tag in _BLOCK_TAGS:
                self._flush()
        if tag == "a":
            href = (d.get("href") or "").strip()
            rel = (d.get("rel") or "").strip()
            self._anchor = [href, rel, []] if href else None

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS or tag == "head":
            if self._skip:
                self._skip -= 1
            return
        if self._skip:
            return
        if tag in ("article", "main"):
            self._region = max(0, self._region - 1)
        if self._anchor is not None and tag == "a":
            text = re.sub(r"\s+", " ", "".join(self._anchor[2])).strip()
            if text:
                self.links.append((self._anchor[0], text, self._anchor[1]))
            self._anchor = None
            return
        if self._boiler:
            self._boiler -= 1
            return
        if self._in_main_body() and tag in _BLOCK_TAGS:
            self._flush()
            self._kind = "p"

    def handle_data(self, data):
        if self._anchor is not None:
            self._anchor[2].append(data)
        if self._skip or self._boiler:
            return
        if self._in_main_body():
            self._buf.append(data)

    def _in_main_body(self):
        return not self.has_main or self._region > 0

    def _flush(self):
        if self._buf:
            text = re.sub(r"[ \t\r\f\v]+", " ", "".join(self._buf))
            text = re.sub(r"\s*\n\s*", " ", text).strip()
            if text:
                self.chunks.append((self._kind, text))
            self._buf = []


def _parse_body(html_text):
    low = html_text[:4000].lower()
    has_main = ("<article" in low or "<main" in low or
                'role="main"' in low or "role='main'" in low)
    p = _ContentParser(has_main)
    try:
        p.feed(html_text)
        p.close()
    except Exception:
        pass
    p._flush()
    return p


# ---------------------------------------------------------------------------
# RSS / Atom branch (feeds advertise themselves as XML)
# ---------------------------------------------------------------------------

class _RSSParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.feed_title = ""
        self.feed_desc = ""
        self.items = []
        self._in_item = 0
        self._tag = None
        self._buf = []
        self._item = {}

    def handle_starttag(self, tag, attrs):
        tag = tag.split(":")[-1].lower()
        if tag in ("item", "entry"):
            self._in_item += 1
            self._item = {}
        elif self._in_item:
            if tag in ("title", "link", "pubdate", "pubDate", "date",
                       "updated", "published", "summary", "description",
                       "content"):
                self._tag = tag
                self._buf = []
                if tag == "link":
                    d = dict(attrs)
                    if d.get("href"):
                        self._buf = [d["href"]]
        elif tag in ("title", "description"):
            self._tag = "feed_" + tag
            self._buf = []

    def handle_endtag(self, tag):
        tag = tag.split(":")[-1].lower()
        text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
        if self._in_item:
            if tag in ("item", "entry"):
                self._in_item -= 1
                if self._item.get("title") or self._item.get("link"):
                    self.items.append(self._item)
                self._item = {}
            elif self._tag:
                if tag == "link" and not self._item.get("link"):
                    if text:
                        self._item["link"] = text
                elif tag in ("summary", "description", "content"):
                    self._item.setdefault("summary", text)
                elif tag == "title":
                    if text:
                        self._item["title"] = text
                elif tag in ("pubdate", "date", "updated", "published"):
                    if text:
                        self._item.setdefault("date", text)
                self._tag = None
                self._buf = []
        else:
            if self._tag == "feed_title" and tag == "title" and text and \
                    not self.feed_title:
                self.feed_title = text
            elif self._tag == "feed_description" and tag == "description" \
                    and text and not self.feed_desc:
                self.feed_desc = text
            self._tag = None
            self._buf = []

    def handle_data(self, data):
        if self._tag or self._in_item:
            self._buf.append(data)


def _strip_tags(s):
    return re.sub(r"<[^>]+>", " ", s or "")


def extract_rss(text):
    p = _RSSParser()
    try:
        p.feed(text)
        p.close()
    except Exception:
        pass
    for it in p.items:
        it["summary"] = _strip_tags(it.get("summary", ""))[:300].strip()
        for key in ("title", "link", "date"):
            it.setdefault(key, "")
    return p


# ---------------------------------------------------------------------------
# Compose the extraction result
# ---------------------------------------------------------------------------

_MD_PREFIX = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### ",
              "h5": "##### ", "h6": "###### ", "li": "- ", "quote": "> "}


def compose(html_text, final_url):
    hp = _HeadParser()
    try:
        hp.feed(html_text)
        hp.close()
    except Exception:
        pass
    ld = _ld_facts(hp.ld_json)
    cp = _parse_body(html_text)

    title = hp.title or ld["headline"]
    published = (hp.published or ld["published"] or
                 (hp.time_attrs[0] if hp.time_attrs else "") or
                 ld["modified"])
    author = hp.author or ld["author"]

    plain = "\n\n".join(t for _, t in cp.chunks)
    md_lines = []
    html_parts = ["<article>"]
    for kind, t in cp.chunks:
        md_lines.append(_MD_PREFIX.get(kind, "") + t)
        if kind in ("h1", "h2", "h3", "h4", "h5", "h6"):
            html_parts.append("<%s>%s</%s>" % (kind, t, kind))
        elif kind == "li":
            html_parts.append("<li>%s</li>" % t)
        elif kind == "quote":
            html_parts.append("<blockquote>%s</blockquote>" % t)
        else:
            html_parts.append("<p>%s</p>" % t)
    html_parts.append("</article>")
    return {
        "url": hp.canonical or final_url,
        "title": title,
        "description": hp.description,
        "publishedTime": published,
        "author": author,
        "lang": hp.lang,
        "site_name": hp.site_name,
        "text": plain,
        "markdown": "\n\n".join(md_lines),
        "html": "\n".join(html_parts),
        "links": cp.links,
    }


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def _net_fail(url, exc):
    sys.stderr.write("glmwr: cannot reach %s (%s)\n" % (url, exc))
    dns_ip, dns_err = _dns_lookup(timeout=5)
    for h in _failure_hints(dns_ip, dns_err):
        sys.stderr.write("glmwr: hint - %s\n" % h)
    return 2


def cmd_read(args):
    url = normalize_url(args.url)
    if not url or " " in url:
        sys.stderr.write("glmwr: invalid URL %r\n" % args.url)
        return 2
    try:
        final_url, status, headers, raw = fetch(url, timeout=args.timeout)
    except Exception as e:
        return _net_fail(url, e)
    if status >= 400:
        sys.stderr.write("glmwr: HTTP %d for %s (page not readable)\n"
                         % (status, url))
        return 1
    mime = (headers.get("Content-Type") or "").lower() \
        if hasattr(headers, "get") else ""
    text = decode_body(raw, None)
    low = text[:1200].lstrip().lower()

    # Branch 1: RSS / Atom feed
    if low.startswith("<?xml") or "<rss" in low[:400] or "<feed" in low[:400]:
        rp = extract_rss(text)
        if rp.items:
            return _print_rss(args, final_url, rp)
        # fall through to generic extraction

    # Branch 2: JSON or plain-text endpoints - raw body IS the content
    if low.startswith("{") or low.startswith("[") or \
            "application/json" in mime or (
            "<html" not in low and "<!doctype html" not in low):
        body = text[:args.max_chars]
        return _print_raw(args, final_url, status, body, mime)

    # Branch 3: HTML page
    r = compose(text, final_url)
    body = r["text"]
    if len(body.strip()) < 60:
        sys.stderr.write("glmwr: page fetched (HTTP %d) but no extractable "
                          "text - likely a JavaScript-only page\n" % status)
        return 1
    return _print_page(args, status, r)


def _print_page(args, status, r):
    if args.json:
        print(json.dumps({
            "code": 0,
            "status": status,
            "data": {
                "url": r["url"],
                "title": r["title"],
                "description": r["description"],
                "publishedTime": r["publishedTime"],
                "author": r["author"],
                "lang": r["lang"],
                "text": r["text"][:args.max_chars],
                "html": r["html"][:args.max_html_chars],
                "linksCount": len(r["links"]),
                "usage": {"tokens": 0},
            },
            "meta": {"usage": {"tokens": 0}},
        }, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print("# %s" % (r["title"] or "(untitled)"))
        if r["description"]:
            print()
            print("> %s" % r["description"])
        print()
        print(r["markdown"][:args.max_chars])
        print()
        print("Source: %s" % r["url"])
        return 0
    print("URL: %s" % r["url"])
    if r["title"]:
        print("Title: %s" % r["title"])
    if r["description"]:
        print("Description: %s" % r["description"])
    if r["publishedTime"]:
        print("Published: %s" % r["publishedTime"])
    if r["author"]:
        print("Author: %s" % r["author"])
    if r["lang"]:
        print("Lang: %s" % r["lang"])
    print("Chars: %d%s" % (
        min(len(r["text"]), args.max_chars),
        " (truncated)" if len(r["text"]) > args.max_chars else ""))
    print()
    print(r["text"][:args.max_chars])
    return 0


def _print_raw(args, final_url, status, body, mime):
    kind = "json" if ((mime and "json" in mime) or
                      body.lstrip()[:1] in ("{", "[")) else "text"
    if args.json:
        print(json.dumps({
            "code": 0,
            "status": status,
            "data": {
                "url": final_url,
                "title": "",
                "description": "",
                "publishedTime": "",
                "author": "",
                "lang": "",
                "text": body,
                "html": "",
                "linksCount": 0,
                "usage": {"tokens": 0},
                "kind": kind,
            },
            "meta": {"usage": {"tokens": 0}},
        }, ensure_ascii=False, indent=2))
        return 0
    print("URL: %s" % final_url)
    print("Kind: raw %s endpoint (no HTML wrapper)" % kind)
    print("Chars: %d%s" % (
        len(body), " (truncated)" if len(body) >= args.max_chars else ""))
    print()
    print(body)
    return 0


def _print_rss(args, final_url, rp):
    items = rp.items[:args.max_items]
    if args.json:
        print(json.dumps({
            "code": 0,
            "status": 200,
            "data": {
                "url": final_url,
                "title": rp.feed_title,
                "description": _strip_tags(rp.feed_desc)[:300].strip(),
                "publishedTime": items[0].get("date", "") if items else "",
                "author": "",
                "lang": "",
                "text": "\n\n".join(
                    "%s\n%s%s" % (it["title"], it["link"],
                                  " (%s)" % it["date"] if it["date"] else "")
                    for it in items),
                "html": "",
                "linksCount": len(rp.items),
                "usage": {"tokens": 0},
                "kind": "rss",
                "items": items,
            },
            "meta": {"usage": {"tokens": 0}},
        }, ensure_ascii=False, indent=2))
        return 0
    print("URL: %s" % final_url)
    print("Kind: RSS/Atom feed (%d items)" % len(rp.items))
    if rp.feed_title:
        print("Feed: %s" % rp.feed_title)
    print()
    for it in items:
        line = "- %s" % (it["title"] or "(untitled)")
        if it["link"]:
            line += "\n  %s" % it["link"]
        if it["date"]:
            line += "  (%s)" % it["date"]
        print(line)
    return 0


def cmd_links(args):
    url = normalize_url(args.url)
    if not url or " " in url:
        sys.stderr.write("glmwr: invalid URL %r\n" % args.url)
        return 2
    try:
        final_url, status, headers, raw = fetch(url, timeout=args.timeout)
    except Exception as e:
        return _net_fail(url, e)
    if status >= 400:
        sys.stderr.write("glmwr: HTTP %d for %s\n" % (status, url))
        return 1
    text = decode_body(raw, None)
    cp = _parse_body(text)
    seen = set()
    rows = []
    for href, label, rel in cp.links:
        href = html_mod.unescape(href)
        if href.startswith("//"):
            href = "https:" + href
        absu = urllib.parse.urljoin(final_url, href)
        if absu.startswith(("mailto:", "javascript:", "tel:", "data:")):
            continue
        if urllib.parse.urlparse(absu).scheme not in ("http", "https"):
            continue
        if absu in seen:
            continue
        seen.add(absu)
        host = urllib.parse.urlparse(absu).netloc
        if args.host:
            want = args.host.lower()
            neg = want.startswith(("!", "-"))
            if want.startswith("@"):
                want = urllib.parse.urlparse(final_url).netloc.lower()
            if neg:
                if want[1:] and want[1:] in host.lower():
                    continue
            elif want not in host.lower():
                continue
        rows.append({"url": absu, "text": label, "rel": rel, "host": host})
        if len(rows) >= args.limit:
            break
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for i, rrow in enumerate(rows, 1):
            print("%d. %s" % (i, rrow["text"] or "(no text)"))
            print("   %s%s" % (
                rrow["url"],
                "  [rel=%s]" % rrow["rel"] if rrow["rel"] else ""))
    if not rows:
        sys.stderr.write("glmwr: zero links extracted (JavaScript-only "
                         "page?)\n")
        return 1
    return 0


def cmd_diagnose(args):
    """Layered connectivity report: env -> DNS -> TCP -> HTTPS -> read."""
    proxies = _proxy_env()
    print("glmwr diagnose - layered network report")
    print("env proxies: %s" % (", ".join("%s=%s" % kv
                                         for kv in sorted(proxies.items()))
                              or "none"))
    print()
    ok = True
    hints = []
    ip, dns_err = _dns_lookup(timeout=args.timeout)
    if dns_err:
        print("[1/4] DNS      resolve %s                     FAIL (%s)"
              % (_DNS_HOST, dns_err))
        ok = False
        hints = _failure_hints(ip, dns_err)
    else:
        print("[1/4] DNS      resolve %s -> %-15s OK" % (_DNS_HOST, ip))
    if ok:
        try:
            sock = socket.create_connection((_DNS_HOST, 443),
                                            timeout=args.timeout)
            sock.close()
            print("[2/4] TCP      connect %s:443                 OK" % _DNS_HOST)
        except OSError as e:
            print("[2/4] TCP      connect %s:443                 FAIL (%s)"
                  % (_DNS_HOST, e))
            ok = False
            hints = ["TCP connect to %s:443 fails while DNS works: a "
                     "firewall or routing block, or a proxy refusing "
                     "CONNECT." % _DNS_HOST]
    if ok:
        try:
            _u, st, _h, raw = fetch(_PROBE_URL, timeout=args.timeout)
            print("[3/4] HTTPS    GET %s  OK (HTTP %d, %d bytes)"
                  % (_PROBE_URL, st, len(raw)))
        except Exception as e:
            print("[3/4] HTTPS    GET %s  FAIL (%s)" % (_PROBE_URL, e))
            ok = False
            hints = ["TLS/HTTP to %s fails while DNS and TCP work: TLS "
                     "interception, a stale CA bundle, or an HTTP-level "
                     "block." % _DNS_HOST]
    if ok:
        try:
            r = compose(decode_body(raw, None), _u)
            if r["title"] and len(r["text"]) > 60:
                print("[4/4] READ     extract page at %s   OK (title=%r, "
                      "%d chars)" % (_DNS_HOST, r["title"][:40],
                                     len(r["text"])))
            else:
                print("[4/4] READ     extract page at %s   FAIL (no text "
                      "extracted; site markup may have changed)" % _DNS_HOST)
                ok = False
                hints = ["The network works but extraction returned no "
                         "text for the probe page - likely a markup change "
                         "upstream; report it."]
        except Exception as e:
            print("[4/4] READ     extract page at %s   FAIL (%s)"
                  % (_DNS_HOST, e))
            ok = False
            hints = ["HTTPS works but the read probe failed (%s). The "
                     "target site is flaky; retry the original URL." % (e,)]
    print()
    if ok:
        print("verdict: outbound network fully working; retry the read.")
        return 0
    print("verdict: outbound network blocked at the layer(s) marked FAIL.")
    for h in hints:
        print("hint - %s" % h)
    return 2


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    ap = argparse.ArgumentParser(
        prog="glmwr.py",
        description=("Zero-dependency web page reader (glm-web-reader "
                     "skill). Extracts title, description, author, "
                     "publication time, plain text and links from any "
                     "URL."))
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("read", help="read one web page (or feed/JSON)")
    r.add_argument("url")
    r.add_argument("--max-chars", type=int, default=4000,
                   help="text cap for output (default 4000)")
    r.add_argument("--max-html-chars", type=int, default=6000,
                   help="simplified HTML cap in --json mode (default 6000)")
    r.add_argument("--max-items", type=int, default=20,
                   help="RSS items shown (default 20)")
    r.add_argument("--json", action="store_true",
                   help="JSON output, field-compatible with the former "
                        "SDK page_reader result")
    r.add_argument("--markdown", action="store_true",
                   help="markdown document output")
    r.add_argument("--timeout", type=float, default=12.0)
    r.set_defaults(func=cmd_read)

    l = sub.add_parser("links", help="list hyperlinks on one page")
    l.add_argument("url")
    l.add_argument("--limit", type=int, default=30,
                   help="max links (default 30)")
    l.add_argument("--host", default=None,
                   help="filter: HOST must match, !HOST excludes, @HOST "
                        "same host as the page")
    l.add_argument("--json", action="store_true",
                   help="JSON array of {url, text, rel, host}")
    l.add_argument("--timeout", type=float, default=12.0)
    l.set_defaults(func=cmd_links)

    d = sub.add_parser(
        "diagnose",
        help="layered network diagnosis: DNS, TCP, HTTPS, page read")
    d.add_argument("--timeout", type=float, default=10.0)
    d.set_defaults(func=cmd_diagnose)

    ap.add_argument("--version", action="version",
                    version="glmwr " + VERSION)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if getattr(args, "limit", None):
        args.limit = max(1, min(args.limit, 200))
    if getattr(args, "max_items", None):
        args.max_items = max(1, min(args.max_items, 50))
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
