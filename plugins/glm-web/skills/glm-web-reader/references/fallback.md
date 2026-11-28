# GLM Web Reader — Connectivity Fallback

Load this file only when `glmwr.py` exits with code 2 (page unreachable),
when the stderr hint lines or `glmwr.py diagnose` report a blocked layer,
or when the user wants to fix page-fetch connectivity. For a plain read
request, SKILL.md is enough.

## Cause #1 (most common): the Codex command sandbox

Symptom: the user's browser opens the page fine, but inside Codex every
read fails with "cannot reach" / "could not resolve host" / DNS errors
and exit 2. The conversation itself keeps working.

Cause: Codex CLI runs agent tool commands inside an OS-level sandbox
(Seatbelt on macOS, Landlock on Linux) that denies network access by
default. Codex's own model traffic - the connection to the model provider
in your config - is sent by the Codex process itself, outside the command
sandbox. That is exactly why the model keeps answering while glmwr.py
cannot resolve anything.

30-second confirmation - run BOTH; the difference is the signal:

```bash
# 1) in YOUR OWN terminal (not inside Codex):
curl -I --max-time 8 https://www.bing.com        # expect HTTP 200/302

# 2) the same test inside Codex - ask the agent to run:
curl -I --max-time 8 https://www.bing.com
# or the layered report:
"${GLM_WEB_READER_PYTHON:-python3}" scripts/glmwr.py diagnose
```

Terminal OK + Codex FAIL at the DNS layer  ->  the sandbox, not the network.

Fix - `~/.codex/config.toml`, then restart Codex:

```toml
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = true
```

macOS caveat (openai/codex#10390): on affected macOS builds the seatbelt
profile silently ignores `network_access = true` - DNS stays blocked inside
Codex even with the config above. After restarting, re-run the in-Codex curl
from the confirmation block; if it still fails, launch Codex with the CLI
flag instead (`codex --sandbox danger-full-access`; per the issue a
config-only `sandbox_mode = "danger-full-access"` may not be enough - the
CLI flag is the reliable form).

Alternatives:

- One-off session: `codex --sandbox danger-full-access` (grants full access -
  only if you accept that).
- `codex --full-auto` is NOT a fix: it still keeps the sandbox network
  blocked. Only the `network_access` config above (or danger-full-access)
  opens it.

Same signature, same fix, when `setup.sh` passes in your terminal but
reads fail inside Codex: sandbox again, not your network.

## Cause #2: proxy environment differs between shells

If you reach the web only through a proxy, the proxy variables must be
visible to Codex's command shell - a proxy exported only in your
interactive terminal does not propagate.

```bash
export HTTPS_PROXY=http://<proxy-host>:<port>
export HTTP_PROXY=http://<proxy-host>:<port>
codex --profile local
```

glmwr.py uses Python's urllib, which honors `HTTPS_PROXY`, `HTTP_PROXY`
and `ALL_PROXY` automatically; `NO_PROXY` exempts hosts as usual. When DNS
fails AND a proxy variable is set, the stderr hints point at the proxy
first - check that the proxy address itself is reachable from that shell.

## Cause #3: the page host itself is down or blocked

Other URLs read fine; only this page fails while DNS of well-known hosts
still resolves. Verify with the same URL in your own terminal
(`curl -I <URL>`). A single unreachable page is the site's problem
(hard-blocked region, expired domain, anti-bot wall): report it, do not
hammer it with retries, and offer an alternative source if you know one.

## Cause #4: the session died on the model server's built-in web_fetch

Symptom: Codex aborts mid-stream with `stream disconnected before
completion: This model requires an Ollama account. Please sign in to
Ollama to use this model.` and the local Ollama log shows a
`POST /api/experimental/web_fetch` request.

Cause: something in the chain reached for the model server's OWN
page-fetch tool instead of glmwr.py. On Ollama that feature is a cloud
service: the local daemon proxies the fetch to ollama.com, and ollama.com
requires a signed-in account (free tier with rate limits, then metered).
Without sign-in the server aborts the stream. glmwr.py never touches that
endpoint - its only network activity is fetching the user's URL directly -
so this crash is not the plugin misbehaving; it is the built-in tool
being triggered.

Fix, in this order:

1. `~/.codex/config.toml`: make sure no built-in web-fetch/web-search tool
   is declared to the provider (delete `web_search = true` from the
   `[tools]` section if present). Restart Codex.
2. Do NOT run `ollama signin` to make the error go away: signing in enables
   the metered cloud path and bypasses glmwr.py entirely.
3. Keep Ollama's experimental web tools off: in the macOS Ollama app turn
   the Web search / web fetch toggles off; with `ollama serve` make sure
   the feature is not enabled server-side.
4. Inspect the model itself: `ollama show <model> --modelfile` - if the
   TEMPLATE declares a `web_fetch` / `web_search` tool, rebuild the model
   from a Modelfile without it, otherwise the model keeps calling a tool
   only the cloud can serve.
5. Model names starting with `hf.co/` trigger the same account check on
   every request; alias them locally (`ollama cp "hf.co/..." local-name`)
   and point Codex at the alias.

Once the session survives, re-check the glmwr.py path with the Cause #1
curl test and re-run the question.

## Cause #5: Ollama runs on a different machine (403, Codex proxy)

Symptom: the session dies at model transport - before or instead of any
tool call - with `unexpected status 403 Forbidden: {"error":"Codex proxy
only accepts loopback requests"}`, and the reported url is the Ollama
machine's `/api/codex/v1/responses` endpoint.

Cause: `/api/codex/v1/*` is Ollama's dedicated Codex-proxy endpoint, and it
accepts only loopback clients by design. When Codex runs on one machine and
the Ollama daemon on another (LAN / 内网), every request to that endpoint is
rejected with 403. This is the model-transport layer, not page reading:
glmwr.py never connects to the model server, so nothing in this plugin
causes or fixes it - the plugin keeps working exactly as before once the
provider URL is corrected.

Fix: see the plugin README's 「远程 Ollama」 section for the three options
with commands (A: point the provider at Ollama's generic /v1 endpoint with
`wire_api = "responses"` - recommended; B: SSH tunnel so the request
arrives as loopback; C: reverse proxy on the Ollama machine). Note: Codex
0.162+ removed `wire_api = "chat"`, so the old chat-wire fallback is not
available on current Codex versions.

## Exit 1 is different: the network worked, the page did not

HTTP 404/5xx, a JavaScript-only page, or zero extractable text is NOT a
connectivity problem - no proxy or sandbox fix will change it. Report the
page as unreadable and move on (or offer an alternative URL). Do not
treat a 404 as an empty page and answer from memory.

## Honest failure wording (pick the matching cause)

Sandbox (browser works, Codex tools do not):

> 读取受限：Codex 的命令沙箱默认禁网（已由 diagnose 确认：Codex 内 DNS 解析失败，而本机终端正常）。修复：在 ~/.codex/config.toml 设置 sandbox_mode = "workspace-write" 并在 [sandbox_workspace_write] 段开启 network_access = true，重启 Codex 后重试。在此之前我无法读取该页面，也不会凭记忆描述它的内容。

Site down / blocked (other causes):

> 页面不可读：目标站点在本网络不可达（exit 2）。已确认非沙箱问题。请确认该 URL 在浏览器可打开；若需要代理，请将代理变量 export 给 Codex 的 shell。在此之前我不会编造该页面的内容。

Page unreadable (exit 1):

> 该页面已请求成功但无可提取正文（HTTP 404/纯前端渲染页面）。我无法读取其内容，也不会编造。建议提供该内容的替代链接。

Do not answer a page question from memory while the read failed without
labeling the answer as unverified background knowledge. Do not recommend
proxy fixes when the sandbox is the cause - the diagnose verdict tells
them apart.
