#!/usr/bin/env python3
"""glmws - zero-dependency web search CLI for the glm-web-search skill.

Local equivalent of the former cloud-SDK web_search function: no SDK, no
API key, no third-party packages. Engine chain (first that answers wins):

    1. Bing HTML        https://www.bing.com/search        (works in CN)
    2. DuckDuckGo HTML  https://html.duckduckgo.com/html/  (blocked in CN)
    3. DuckDuckGo Lite  https://lite.duckduckgo.com/lite/

Everything is parsed with the Python standard library only
(urllib.request + html.parser). Output schema is field-compatible with
the original SearchFunctionResultItem: url, name, snippet, host_name,
rank, date, favicon.

Subcommands: search, fetch, diagnose.

On total engine failure (exit 2) the CLI prints layered hints on stderr
that separate the common causes (Codex command sandbox vs proxy vs
firewall). `glmws.py diagnose` prints the full layer-by-layer report:
DNS -> TCP -> HTTPS -> engine chain.

Exit codes:
    0  success (>=1 result, or page fetched)
    1  engines answered but zero results (try different keywords)
    2  network/usage error (all engines unreachable, bad arguments)
"""

import argparse
import base64
import concurrent.futures
import html as html_mod
import json
import os
import re
import socket
import sys
import time
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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "identity",  # keep plain HTTP: no gzip to decode
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}

# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def http_get(url, data=None, timeout=12, extra_headers=None):
    """GET/POST a URL, return (final_url, decoded_text). Raises on error."""
    headers = dict(HEADERS)
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read(1_000_000)  # cap at ~1 MB
        charset = resp.headers.get_content_charset() or "utf-8"
        try:
            text = raw.decode(charset, errors="replace")
        except LookupError:
            text = raw.decode("utf-8", errors="replace")
        return resp.geturl(), text


# ---------------------------------------------------------------------------
# URL un-wrapping (Bing /ck/a redirect links, DDG /l/?uddg= links)
# ---------------------------------------------------------------------------

def _decode_bing_ck(url):
    """https://www.bing.com/ck/a?...&u=a1<base64url> -> real URL."""
    try:
        q = urllib.parse.urlparse(url)
        if "bing.com" not in (q.netloc or "").lower():
            return url
        if not (q.path or "").startswith("/ck/"):
            return url
        qs = urllib.parse.parse_qs(q.query)
        u = (qs.get("u") or [""])[0]
        if not u.startswith("a1"):
            return url
        b64 = u[2:]
        b64 += "=" * (-len(b64) % 4)
        return base64.urlsafe_b64decode(b64).decode("utf-8", errors="replace")
    except Exception:
        return url


def _decode_ddg_l(url):
    """//duckduckgo.com/l/?uddg=<encoded> -> real URL."""
    try:
        if url.startswith("//"):
            url = "https:" + url
        q = urllib.parse.urlparse(url)
        if "duckduckgo.com" not in (q.netloc or "").lower():
            return url
        if not (q.path or "").startswith("/l/"):
            return url
        qs = urllib.parse.parse_qs(q.query)
        uddg = (qs.get("uddg") or [""])[0]
        return uddg or url
    except Exception:
        return url


def unwrap(url):
    url = html_mod.unescape(url or "")
    url = _decode_bing_ck(url)
    url = _decode_ddg_l(url)
    return url.strip()


def host_of(url):
    try:
        netloc = urllib.parse.urlparse(url).netloc
        return urllib.parse.urlsplit("//" + netloc).hostname or netloc
    except Exception:
        return ""


def favicon_of(url):
    host = host_of(url)
    if not host:
        return ""
    return "https://icons.duckduckgo.com/ip3/%s.ico" % host


# ---------------------------------------------------------------------------
# Network diagnosis (why did all engines fail?)
# ---------------------------------------------------------------------------

_DNS_HOST = "www.bing.com"
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
        return ["DNS works (%s -> %s) but engines were unreachable: a "
                "TCP/TLS-level block (firewall, proxy ports) or engine "
                "outage. Run: glmws.py diagnose" % (_DNS_HOST, dns_ip)]
    proxies = _proxy_env()
    if proxies:
        return ["DNS fails and a proxy is configured (%s). If that proxy "
                "is unreachable from this shell, every lookup breaks; "
                "fix or unset the proxy variables."
                % ", ".join(sorted(proxies))]
    return list(_SANDBOX_HINTS)


# ---------------------------------------------------------------------------
# Date extraction from snippet text
# ---------------------------------------------------------------------------

_REL_UNITS = {"second": 1, "minute": 60, "hour": 3600, "day": 86400,
              "week": 604800, "month": 2592000, "year": 31536000}
_REL_RE = re.compile(
    r"(\d+)\s*(seconds?|minutes?|hours?|days?|weeks?|months?|years?)\s+ago",
    re.I)
_REL_ZH_RE = re.compile(
    r"(\d+)\s*(秒|分钟|小时|天|周|个?月|年)前")
_MONTHS = {m.lower(): i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}
_ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_EN_DATE_RE = re.compile(
    r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b")
_ZH_DATE_RE = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")


def _mk(year, month, day):
    import calendar
    try:
        return calendar.timegm((year, month, day, 12, 0, 0, 0, 0, 0))
    except Exception:
        return None


def extract_epoch(text):
    """Best-effort epoch seconds from a snippet. None if not found."""
    if not text:
        return None
    m = _REL_RE.search(text)
    if m:
        n = int(m.group(1))
        unit = m.group(2).lower().rstrip("s")
        return time.time() - n * _REL_UNITS.get(unit, 0)
    m = _REL_ZH_RE.search(text)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        mult = {"秒": 1, "分钟": 60, "小时": 3600, "天": 86400,
                "周": 604800, "月": 2592000, "年": 31536000}.get(
            unit.replace("个", ""), 0)
        return time.time() - n * mult
    if "刚刚" in text or "just now" in text.lower():
        return time.time()
    m = _ISO_RE.search(text)
    if m:
        return _mk(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = _ZH_DATE_RE.search(text)
    if m:
        return _mk(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = _EN_DATE_RE.search(text)
    if m:
        mon = _MONTHS.get(m.group(1)[:3].lower())
        if mon:
            return _mk(int(m.group(3)), mon, int(m.group(2)))
    return None


def find_date_text(text):
    """Return the human-readable date fragment of a snippet, or ''."""
    if not text:
        return ""
    for rx in (_REL_RE, _REL_ZH_RE):
        m = rx.search(text)
        if m:
            return m.group(0)
    m = _ISO_RE.search(text)
    if m:
        return m.group(0)
    m = _ZH_DATE_RE.search(text)
    if m:
        return m.group(0)
    m = _EN_DATE_RE.search(text)
    if m:
        return m.group(0)
    return ""


# ---------------------------------------------------------------------------
# Parsers (stdlib HTMLParser state machines, one per engine)
# ---------------------------------------------------------------------------

class _BaseSERPParser(HTMLParser):
    """Shared machinery: collect (url, title, snippet) result tuples."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.results = []          # list of dicts: url,name,snippet
        self._buf = None           # current text buffer
        self._capture = None       # what the buffer means

    def _start_capture(self, kind):
        if self._buf is None:
            self._buf = []
            self._capture = kind

    def _stop_capture(self):
        text = "".join(self._buf or []).strip()
        text = re.sub(r"\s+", " ", text)
        self._buf = None
        self._capture = None
        return text

    def handle_data(self, data):
        if self._buf is not None:
            self._buf.append(data)

    def handle_entityref(self, name):  # pragma: no cover
        if self._buf is not None:
            self._buf.append(html_mod.unescape("&%s;" % name))


class BingParser(_BaseSERPParser):
    """<li class="b_algo"> blocks: h2>a (title/url), .b_caption p (snippet)."""

    def __init__(self):
        super().__init__()
        self._depth = -1           # -1 outside any b_algo block
        self._cur = None
        self._in_h2 = False
        self._in_caption = False
        self._p_open = False

    @staticmethod
    def _classes(attrs):
        for k, v in attrs:
            if k == "class" and v:
                return set(v.split())
        return set()

    def handle_starttag(self, tag, attrs):
        cls = self._classes(attrs)
        if tag == "li" and "b_algo" in cls and self._depth < 0:
            self._depth = 0
            self._cur = {"url": "", "name": "", "snippet": ""}
            self._in_h2 = self._in_caption = self._p_open = False
            return
        if self._depth < 0:
            return
        if tag == "li":
            self._depth += 1
        elif tag == "h2" and not self._in_caption:
            self._in_h2 = True
            if not self._cur["url"]:
                for k, v in attrs:
                    if k == "href" and v:
                        self._cur["url"] = unwrap(v)
        elif tag == "a" and self._in_h2:
            if not self._cur["url"]:
                for k, v in attrs:
                    if k == "href" and v:
                        self._cur["url"] = unwrap(v)
            self._start_capture("title")
        elif tag == "div" and "b_caption" in cls:
            self._in_caption = True
        elif tag == "p" and self._in_caption and not self._p_open:
            self._p_open = True
            self._start_capture("snippet")

    def handle_endtag(self, tag):
        if self._depth < 0:
            return
        if tag == "p" and self._p_open:
            text = self._stop_capture()
            if not self._cur["snippet"]:
                self._cur["snippet"] = text
            self._p_open = False
        elif tag == "a" and self._capture == "title":
            text = self._stop_capture()
            if not self._cur["name"]:
                self._cur["name"] = text
        elif tag == "h2" and self._in_h2:
            self._in_h2 = False
        elif tag == "div" and self._in_caption and self._capture is None:
            self._in_caption = False
        elif tag == "li":
            self._depth -= 1
            if self._depth < 0:
                self._depth = -1
                c = self._cur or {}
                if c.get("url") and c.get("name"):
                    self.results.append(c)
                self._cur = None

    def feed_all(self, text):
        self.reset()
        self.feed(text)
        # close any dangling block
        if self._cur is not None and self._depth >= 0:
            if self._cur.get("url") and self._cur.get("name"):
                self.results.append(self._cur)
            self._cur = None


class DDGHTMLParser(_BaseSERPParser):
    """DuckDuckGo html endpoint: a.result__a (url/title), a.result__snippet."""

    def __init__(self):
        super().__init__()
        self._cur = None
        self._kind = None  # 'title' | 'snippet'

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        cls = set((d.get("class") or "").split())
        if tag == "a":
            if "result__a" in cls:
                self._cur = {"url": unwrap(d.get("href") or ""),
                             "name": "", "snippet": ""}
                self._kind = "title"
                self._start_capture("title")
            elif "result__snippet" in cls and self._cur is not None:
                self._kind = "snippet"
                self._start_capture("snippet")

    def handle_endtag(self, tag):
        if tag != "a":
            return
        if self._capture == "title":
            text = self._stop_capture()
            if self._cur is not None:
                self._cur["name"] = text
                if self._cur["url"] and text:
                    self.results.append(self._cur)
                self._cur = None
        elif self._capture == "snippet":
            text = self._stop_capture()
            if self._cur is not None:
                self._cur["snippet"] = text
        self._kind = None

    def feed_all(self, text):
        self.reset()
        self.feed(text)


class DDGLiteParser(DDGHTMLParser):
    """DuckDuckGo lite endpoint: a.result-link / td.result-snippet."""

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        cls = set((d.get("class") or "").split())
        if tag == "a" and "result-link" in cls:
            self._cur = {"url": unwrap(d.get("href") or ""),
                         "name": "", "snippet": ""}
            self._start_capture("title")
        elif tag == "td" and "result-snippet" in cls and self._cur is not None:
            self._start_capture("snippet")

    def handle_endtag(self, tag):
        if tag == "a" and self._capture == "title":
            text = self._stop_capture()
            if self._cur is not None:
                self._cur["name"] = text
                if self._cur["url"] and text:
                    self.results.append(self._cur)
                self._cur = None
        elif tag == "td" and self._capture == "snippet":
            text = self._stop_capture()
            if self._cur is not None:
                self._cur["snippet"] = text


# ---------------------------------------------------------------------------
# Engines
# ---------------------------------------------------------------------------

def _try_times(fn, attempts=2, delay=1.5):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last = e
            if i + 1 < attempts:
                time.sleep(delay)
    raise last


def engine_bing(query, num, market=None, timeout=12):
    out = []
    seen = set()
    first = 1
    for _page in range(4):  # at most 4 pages (~40 results)
        q = urllib.parse.quote_plus(query)
        url = ("https://www.bing.com/search?q=%s&count=10&first=%d"
               % (q, first))
        if market:
            url += "&mkt=%s" % urllib.parse.quote_plus(market)
        _u, text = _try_times(lambda: http_get(url, timeout=timeout))
        p = BingParser()
        p.feed_all(text)
        new = 0
        for r in p.results:
            if r["url"] and r["url"] not in seen:
                seen.add(r["url"])
                out.append(r)
                new += 1
        if new == 0 or len(out) >= num:
            break
        first += 10
    return out


def engine_ddg_html(query, num, market=None, timeout=12):
    data = urllib.parse.urlencode({"q": query}).encode("ascii")
    _u, text = _try_times(
        lambda: http_get("https://html.duckduckgo.com/html/",
                         data=data, timeout=timeout))
    p = DDGHTMLParser()
    p.feed_all(text)
    return p.results[:max(num, 1)]


def engine_ddg_lite(query, num, market=None, timeout=12):
    q = urllib.parse.quote_plus(query)
    _u, text = _try_times(
        lambda: http_get("https://lite.duckduckgo.com/lite/?q=%s" % q,
                         timeout=timeout))
    p = DDGLiteParser()
    p.feed_all(text)
    return p.results[:max(num, 1)]


ENGINES = [
    ("bing", engine_bing, "Bing HTML"),
    ("ddg", engine_ddg_html, "DuckDuckGo HTML"),
    ("ddg-lite", engine_ddg_lite, "DuckDuckGo Lite"),
]


def run_search(query, num, engine="auto", market=None, timeout=12):
    """Return (items, engine_label, had_network_error).

    items: list of SearchFunctionResultItem-compatible dicts.
    had_network_error: True when every attempted engine raised.
    """
    chain = [e for e in ENGINES if engine == "auto" or e[0] == engine]
    if not chain:
        raise SystemExit(2)
    net_fail = True  # becomes False once any engine answers over HTTP
    last_err = None
    for key, fn, label in chain:
        try:
            raw = fn(query, num, market=market, timeout=timeout)
        except Exception as e:
            last_err = e
            continue  # engine down: fall through to the next one
        net_fail = False
        items = []
        for i, r in enumerate(raw[:num]):
            url = r.get("url", "")
            if not url.startswith("http"):
                continue
            snippet = r.get("snippet", "")
            items.append({
                "url": url,
                "name": r.get("name", "") or "(untitled)",
                "snippet": snippet,
                "host_name": host_of(url),
                "rank": i + 1,
                "date": find_date_text(snippet),
                "favicon": favicon_of(url),
            })
        if items:
            return items, label, False
    if net_fail:
        sys.stderr.write("glmws: all engines unreachable%s\n" %
                         (" (%s)" % last_err if last_err else ""))
        return [], "", True
    return [], "", False


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def print_text(items, engine_label, query):
    print("Search Results:")
    print("================")
    print("query: %s" % query)
    print("engine: %s" % (engine_label or "n/a"))
    print()
    for it in items:
        print("%d. %s" % (it["rank"], it["name"]))
        print("   URL: %s" % it["url"])
        print("   Snippet: %s" % (it["snippet"] or "-"))
        print("   Host: %s" % (it["host_name"] or "-"))
        print("   Date: %s" % (it["date"] or "-"))
        print()
    print("Total results: %d" % len(items))


def print_markdown(items, engine_label):
    for it in items:
        line = "- [%s](%s)" % (it["name"], it["url"])
        if it.get("snippet"):
            line += " — %s" % it["snippet"]
        print(line)


# ---------------------------------------------------------------------------
# fetch subcommand: read one page, extract readable text
# ---------------------------------------------------------------------------

_SKIP_TAGS = {"script", "style", "noscript", "nav", "footer", "header",
              "svg", "form", "button", "iframe"}
_BLOCK_TAGS = {"p", "div", "li", "tr", "td", "th", "section", "article",
               "h1", "h2", "h3", "h4", "h5", "h6", "br", "blockquote",
               "pre", "dd", "dt"}


class _PageTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.chunks = []
        self._skip = 0
        self._in_title = False
        self._meta_name = None
        self._meta_content = ""
        self._buf = None
        self._cur_text = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in _SKIP_TAGS:
            self._skip += 1
        elif tag == "title":
            self._in_title = True
            self._buf = []
        elif tag == "meta":
            name = (d.get("name") or d.get("property") or "").lower()
            content = d.get("content") or ""
            if name in ("description", "og:description", "twitter:description"):
                if content and not self.description:
                    self.description = re.sub(r"\s+", " ", content).strip()
        elif self._skip == 0 and tag in _BLOCK_TAGS:
            self._flush()
        if self._skip == 0 and self._in_title is False and tag not in _SKIP_TAGS:
            pass  # plain inline text handled in handle_data

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip:
            self._skip -= 1
        elif tag == "title":
            self._in_title = False
            if self._buf is not None:
                self.title = re.sub(r"\s+", " ", "".join(self._buf)).strip()
                self._buf = None
        elif tag in _BLOCK_TAGS:
            self._flush()

    def handle_data(self, data):
        if self._in_title and self._buf is not None:
            self._buf.append(data)
        elif self._skip == 0:
            self._cur_text.append(data)

    def _flush(self):
        if self._cur_text:
            text = re.sub(r"\s+", " ", "".join(self._cur_text)).strip()
            if text:
                self.chunks.append(text)
            self._cur_text = []


def extract_page(html_text):
    p = _PageTextParser()
    try:
        p.feed(html_text)
        p.close()
    except Exception:
        pass
    body = "\n\n".join(p.chunks)
    return p.title, p.description, body


def cmd_fetch(args):
    url = args.url
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    try:
        final_url, text = http_get(url, timeout=args.timeout)
    except urllib.error.HTTPError as e:
        sys.stderr.write("glmws: HTTP %s for %s\n" % (e.code, url))
        return 2
    except Exception as e:
        sys.stderr.write("glmws: fetch failed for %s (%s)\n" % (url, e))
        return 2
    low = text[:2000].lstrip().lower()
    if low.startswith("{") or low.startswith("["):
        body = text[:args.max_chars]
        title = ""
        desc = ""
    elif "<html" in low or "<!doctype html" in low:
        title, desc, body = extract_page(text)
    else:
        title, desc, body = "", "", text
    print("URL: %s" % final_url)
    if title:
        print("Title: %s" % title)
    if desc:
        print("Description: %s" % desc)
    print("Chars: %d%s" % (
        min(len(body), args.max_chars),
        " (truncated)" if len(body) > args.max_chars else ""))
    print()
    print(body[:args.max_chars])
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_search(args):
    query = args.query.strip()
    if not query:
        sys.stderr.write("glmws: empty query\n")
        return 2
    try:
        items, label, net_err = run_search(
            query, args.num, engine=args.engine,
            market=args.market, timeout=args.timeout)
    except SystemExit:
        raise
    if net_err:
        dns_ip, dns_err = _dns_lookup(timeout=5)
        for h in _failure_hints(dns_ip, dns_err):
            sys.stderr.write("glmws: hint - %s\n" % h)
        return 2
    if args.recency_days and items:
        cutoff = time.time() - args.recency_days * 86400
        kept = []
        for it in items:
            ep = extract_epoch(it["snippet"])
            if ep is None or ep >= cutoff:
                kept.append(it)
        dropped = len(items) - len(kept)
        items = kept
        if dropped:
            sys.stderr.write("glmws: dropped %d result(s) older than %d day(s)\n"
                             % (dropped, args.recency_days))
    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return 0 if items else 1
    if args.markdown:
        print_markdown(items, label)
        return 0 if items else 1
    if not items:
        sys.stderr.write("glmws: zero results for %r (engines reachable; "
                         "try different keywords)\n" % query)
        return 1
    print_text(items, label, query)
    return 0


def cmd_diagnose(args):
    """Layered connectivity report: env -> DNS -> TCP -> HTTPS -> engines."""
    proxies = _proxy_env()
    print("glmws diagnose - layered network report")
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
            _u, text = http_get("https://%s/" % _DNS_HOST,
                                timeout=args.timeout)
            print("[3/4] HTTPS    GET https://%s/            OK (%d bytes)"
                  % (_DNS_HOST, len(text)))
        except Exception as e:
            print("[3/4] HTTPS    GET https://%s/            FAIL (%s)"
                  % (_DNS_HOST, e))
            ok = False
            hints = ["TLS/HTTP to %s fails while DNS and TCP work: TLS "
                     "interception, a stale CA bundle, or an HTTP-level "
                     "block." % _DNS_HOST]
    if ok:
        items, label, net_err = run_search("connectivity probe", 1,
                                           timeout=args.timeout)
        if items:
            print("[4/4] ENGINE   search probe (engine chain)    OK (%s)"
                  % label)
        else:
            print("[4/4] ENGINE   search probe (engine chain)    FAIL")
            ok = False
            if net_err:
                hints = ["HTTPS to %s works but the engine chain raises; "
                         "the /search path may be blocked (403 or a "
                         "redirect loop). Retry with --engine bing."
                         % _DNS_HOST]
            else:
                hints = ["Engines answer the network but return zero "
                         "usable results; likely engine markup changes - "
                         "report upstream."]
    print()
    if ok:
        print("verdict: outbound network fully working; retry the query.")
        return 0
    print("verdict: outbound network blocked at the layer(s) marked FAIL.")
    for h in hints:
        print("hint - %s" % h)
    return 2


def build_parser():
    ap = argparse.ArgumentParser(
        prog="glmws.py",
        description=("Zero-dependency web search (glm-web-search skill). "
                     "Engines: Bing HTML -> DuckDuckGo HTML -> DuckDuckGo Lite."))
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="search the web")
    s.add_argument("query")
    s.add_argument("--num", type=int, default=10,
                   help="number of results (default 10, max 40)")
    s.add_argument("--recency-days", type=int, default=None,
                   help="drop results older than N days (best-effort)")
    s.add_argument("--json", action="store_true",
                   help="output JSON array (SearchFunctionResultItem schema)")
    s.add_argument("--markdown", action="store_true",
                   help="output markdown link list")
    s.add_argument("--engine", default="auto",
                   choices=["auto", "bing", "ddg", "ddg-lite"])
    s.add_argument("--market", default=None,
                   help="Bing market, e.g. zh-CN or en-US (optional)")
    s.add_argument("--timeout", type=float, default=12.0)
    s.set_defaults(func=cmd_search)

    f = sub.add_parser("fetch", help="read one web page as plain text")
    f.add_argument("url")
    f.add_argument("--max-chars", type=int, default=4000)
    f.add_argument("--timeout", type=float, default=12.0)
    f.set_defaults(func=cmd_fetch)

    d = sub.add_parser(
        "diagnose",
        help="layered network diagnosis: DNS, TCP, HTTPS, engine chain")
    d.add_argument("--timeout", type=float, default=10.0)
    d.set_defaults(func=cmd_diagnose)

    ap.add_argument("--version", action="version",
                    version="glmws " + VERSION)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if getattr(args, "num", None):
        args.num = max(1, min(args.num, 40))
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
