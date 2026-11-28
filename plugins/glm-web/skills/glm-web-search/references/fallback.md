# GLM Web Search — Connectivity Fallback

Load this file only when `glmws.py` exits with code 2 (no engine reachable),
when the stderr hint lines or `glmws.py diagnose` report a blocked layer, or
when the user wants to fix search connectivity. For a plain question,
SKILL.md is enough.

## Cause #1 (most common): the Codex command sandbox

Symptom: the user's browser opens www.bing.com fine and DuckDuckGo is
blocked (normal in mainland CN), but inside Codex every engine fails with
"could not resolve host" / DNS errors and exit 2. The conversation itself
keeps working.

Cause: Codex CLI runs agent tool commands inside an OS-level sandbox
(Seatbelt on macOS, Landlock on Linux) that denies network access by
default. Codex's own model traffic - the connection to the model provider
in your config - is sent by the Codex process itself, outside the command
sandbox. That is exactly why the model keeps answering while glmws.py
cannot resolve anything.

30-second confirmation - run BOTH; the difference is the signal:

```bash
# 1) in YOUR OWN terminal (not inside Codex):
curl -I --max-time 8 https://www.bing.com        # expect HTTP 200/302

# 2) the same test inside Codex - ask the agent to run:
curl -I --max-time 8 https://www.bing.com
# or the layered report:
"${GLM_WEB_SEARCH_PYTHON:-python3}" scripts/glmws.py diagnose
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
searches fail inside Codex: sandbox again, not your network.

## Cause #2: proxy environment differs between shells

If you reach the web only through a proxy, the proxy variables must be
visible to Codex's command shell - a proxy exported only in your
interactive terminal does not propagate.

```bash
export HTTPS_PROXY=http://<proxy-host>:<port>
export HTTP_PROXY=http://<proxy-host>:<port>
codex --profile local
```

`glmws.py` uses Python's urllib, which honors `HTTPS_PROXY`, `HTTP_PROXY`
and `ALL_PROXY` automatically; `NO_PROXY` exempts hosts as usual. When DNS
fails AND a proxy variable is set, the stderr hints point at the proxy
first - check that the proxy address itself is reachable from that shell.

## Cause #3: machine truly offline or DNS broken

`curl -I https://www.bing.com` fails in your own terminal too, and
`glmws.py diagnose` fails at the DNS layer with no proxy configured. Fix
base connectivity (router, VPN, DNS resolver) - nothing engine-side will
help. Note DuckDuckGo endpoints are unreachable from most mainland CN
networks by design; Bing HTML is the primary engine there.

## Cause #4: the session died on the model server's built-in web_search

Symptom: Codex aborts mid-stream with `stream disconnected before
completion: This model requires an Ollama account. Please sign in to
Ollama to use this model.` and the local Ollama log shows a
`POST /api/experimental/web_search` request.

Cause: something in the chain reached for the model server's OWN web-search
tool instead of glmws.py. On Ollama that feature is a cloud service: the
local daemon proxies the query to ollama.com, and ollama.com requires a
signed-in account (free tier with rate limits, then metered). Without
sign-in the server aborts the stream. glmws.py never touches that endpoint
- its only network targets are Bing and the two DuckDuckGo mirrors listed
in SKILL.md - so this crash is not the plugin misbehaving; it is the
built-in tool being triggered.

Fix, in this order:

1. `~/.codex/config.toml`: delete `web_search = true` from the `[tools]`
   section if present, so Codex stops declaring the built-in tool to the
   provider. Restart Codex.
2. Do NOT run `ollama signin` to make the error go away: signing in enables
   the metered cloud search path and bypasses glmws.py entirely.
3. Keep Ollama's experimental web search off: in the macOS Ollama app turn
   the Web search toggle off; with `ollama serve` make sure the feature is
   not enabled server-side.
4. Inspect the model itself: `ollama show <model> --modelfile` - if the
   TEMPLATE declares a `web_search` / `web_fetch` tool, rebuild the model
   from a Modelfile without it, otherwise the model keeps calling a tool
   only the cloud can serve.
5. Model names starting with `hf.co/` trigger the same account check on
   every request; alias them locally (`ollama cp "hf.co/..." local-name`)
   and point Codex at the alias.

Once the session survives, re-check the glmws.py path with the Cause #1
curl test and re-run the question.

## Reading a known URL without any engine

`fetch` does not depend on the search engines, but it is subject to the
same sandbox - if DNS fails for engines it fails for fetch too (see Cause
#1). When even direct fetch fails, the machine is offline for that site:
say so and stop. Do not guess page contents, and do not treat the failed
search as an empty result set - report the failure itself.

## Honest failure wording (pick the matching cause)

Sandbox (browser works, Codex tools do not):

> 搜索受限：Codex 的命令沙箱默认禁网（已由 diagnose 确认：Codex 内 DNS 解析失败，而本机终端正常）。修复：在 ~/.codex/config.toml 设置 sandbox_mode = "workspace-write" 并在 [sandbox_workspace_write] 段开启 network_access = true，重启 Codex 后重试。在此之前我无法联网检索，也不会编造来源。

Proxy / offline (other causes):

> 网络受限：搜索引擎均不可达（exit 2）。已尝试 Bing 与 DuckDuckGo 备用链。请检查本机出网/代理设置（curl -I https://www.bing.com）；确认代理变量已 export 给 Codex 的 shell。在此之前我无法提供联网检索结果，也不会编造来源。

Do not answer a search question from memory while search is down without
labeling the answer as unverified background knowledge. Do not recommend
proxy fixes when the sandbox is the cause - the diagnose verdict tells
them apart.
