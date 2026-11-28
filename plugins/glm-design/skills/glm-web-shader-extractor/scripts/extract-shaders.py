#!/usr/bin/env python3
"""
extract-shaders.py — extract GLSL shader strings from minified JS bundles
WITHOUT loading the bundle into the model context.

This is the Codex-native replacement for the original skill's
"spawn a subagent to analyse the 1MB+ bundle" step (Codex has no subagents):
the bundle stays on disk, only a compact summary reaches stdout, and every
extracted shader lands in its own file for on-demand reading.

Usage:
  python3 extract-shaders.py <bundle.js> [bundle2.js ...] [--out DIR]
                              [--min-score N] [--preview N]

Output:
  stdout   — compact summary (counts, vertex/fragment split, uniform list,
             ${template} injections, TSL signals, file index)
  out dir  — one .glsl file per extracted shader (default /tmp/extracted-shaders)

Exit codes:
  0  at least one shader extracted
  1  no shader-like string found (or file missing / not readable)
  2  target file cannot be read at all

Zero dependencies: Python standard library only.
"""

import argparse
import json
import os
import re
import sys

GLSL_SCORES = {
    # strongly indicative of GLSL source inside a JS string
    "void main": 4,
    "gl_FragColor": 6,
    "gl_Position": 6,
    "gl_PointCoord": 6,
    "gl_PointSize": 5,
    "precision mediump": 3,
    "precision highp": 3,
    "#version 300 es": 6,
    "#version 100": 4,
    "sampler2D": 5,
    "samplerCube": 5,
    "texture2D": 4,
    "texture(": 3,
    "smoothstep(": 2,
    "varying ": 3,
    "attribute vec": 3,
    "uniform vec": 3,
    "uniform float": 3,
    "uniform mat": 3,
    "uniform int": 2,
    "in vec": 2,
    "out vec": 2,
    "out float": 2,
    "FRAGMENT_SHADER": 1,   # JS constant, weak signal alone
    "VERTEX_SHADER": 1,
    "discard;": 3,
    "mix(": 1,
    "vec3(": 1,
    "vec4(": 1,
    "fract(": 1,
}

UNIFORM_RE = re.compile(r"\buniform\s+(?:highp\s+|mediump\s+|lowp\s+)?"
                        r"(?:float|int|bool|vec[234]|mat[234](?:x[234])?|sampler2D|samplerCube)\s+"
                        r"([A-Za-z_][A-Za-z0-9_]*)")
VARYING_RE = re.compile(r"\b(?:varying|out)\s+(?:highp\s+)?(?:float|vec[234])\s+"
                        r"([A-Za-z_][A-Za-z0-9_]*)")
TEMPLATE_RE = re.compile(r"\$\{([A-Za-z_$][A-Za-z0-9_$.]*(?:\([A-Za-z0-9_$\"']*\))?)")  # ${Vt} / ${pe("x")}
TSL_SIGNALS = [".mul(", ".add(", ".sub(", ".div(", ".toVar(", ".assign(",
               ".oneMinus()", ".sample(", "Fn(", "convertToTexture(", "timerLocal("]


def scan_string_literals(text):
    """Yield (quote, content) for every string literal in JS source.

    A simple character scanner: tracks quote state, honours backslash escapes,
    and treats a newline inside ' or " as unterminated (restarts cleanly).
    Regex literals may occasionally yield false strings; the GLSL scoring
    below filters those out because they lack GLSL features.
    """
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in "'\"`":
            quote = c
            i += 1
            buf = []
            while i < n:
                ch = text[i]
                if ch == "\\":
                    nxt = text[i + 1] if i + 1 < n else ""
                    mapping = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\",
                               "'": "'", '"': '"', "`": "`", "0": "\0"}
                    buf.append(mapping.get(nxt, nxt))
                    i += 2
                    continue
                # a ${...} injection inside a plain-quoted shader string may
                # itself contain quotes (e.g. ${pe("x")}) — skip the whole
                # placeholder so the shader is not truncated mid-string
                if ch == "$" and text[i:i + 2] == "${":
                    close = text.find("}", i + 2)
                    if close != -1:
                        buf.append(text[i:close + 1])
                        i = close + 1
                        continue
                if ch == quote:
                    i += 1
                    break
                if ch == "\n" and quote != "`":
                    break  # unterminated single/double-quote string
                buf.append(ch)
                i += 1
            yield quote, "".join(buf)
        else:
            i += 1


def score_glsl(s):
    total = 0
    hits = []
    for token, w in GLSL_SCORES.items():
        occurrences = s.count(token)
        if occurrences:
            total += w * (1 if occurrences == 1 else 2)
            hits.append(token)
    return total, hits


def classify(s):
    frag = ("gl_FragColor" in s or "gl_PointCoord" in s or
            ("out vec4" in s and "void main" in s and "gl_Position" not in s))
    vert = "gl_Position" in s
    if frag and vert:
        return "both"
    if frag:
        return "fragment"
    if vert:
        return "vertex"
    if "void main" in s:
        return "unknown"
    return "unknown"


def main():
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.splitlines()[1])
    ap.add_argument("files", nargs="+", help="JS bundle file(s) to scan")
    ap.add_argument("--out", default="/tmp/extracted-shaders",
                    help="output directory for extracted .glsl files")
    ap.add_argument("--min-score", type=int, default=8,
                    help="minimum GLSL score for a string to count as shader")
    ap.add_argument("--preview", type=int, default=72,
                    help="characters of preview per shader in the index")
    ns = ap.parse_args()

    readable = []
    missing = []
    for f in ns.files:
        if os.path.isfile(f):
            readable.append(f)
        else:
            missing.append(f)
    if missing:
        print(f"unreadable (exit 2): {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)

    os.makedirs(ns.out, exist_ok=True)

    index = []
    all_uniforms = {}
    all_varyings = set()
    all_templates = {}
    tsl_hits = {}
    total_bytes = 0
    total_literals = 0

    for path in readable:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        total_bytes += len(text)

        for sig in TSL_SIGNALS:
            c = text.count(sig)
            if c:
                tsl_hits[sig] = tsl_hits.get(sig, 0) + c

        for _quote, content in scan_string_literals(text):
            total_literals += 1
            if len(content) < 40:
                continue
            score, _hits = score_glsl(content)
            if score < ns.min_score:
                continue
            kind = classify(content)
            index.append({
                "source": os.path.basename(path),
                "kind": kind,
                "chars": len(content),
                "score": score,
                "content": content,
            })
            for m in UNIFORM_RE.finditer(content):
                all_uniforms[m.group(1)] = all_uniforms.get(m.group(1), 0) + 1
            for m in VARYING_RE.finditer(content):
                all_varyings.add(m.group(1))
            for m in TEMPLATE_RE.finditer(content):
                all_templates[m.group(1)] = all_templates.get(m.group(1), 0) + 1

    if not index:
        print(f"No shader-like strings found (scanned {len(readable)} file(s), "
              f"{total_literals} string literals, min-score {ns.min_score}). "
              "Lower --min-score, or the page may use TSL (see references/tsl-extraction.md).")
        sys.exit(1)

    # write each shader to disk
    written = []
    for i, entry in enumerate(index, start=1):
        fname = f"shader-{i:02d}-{entry['kind']}-{entry['source']}.glsl"
        fpath = os.path.join(ns.out, fname)
        with open(fpath, "w", encoding="utf-8") as fh:
            fh.write(entry["content"])
        entry["file"] = fname
        written.append(fpath)

    kinds = {}
    for e in index:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1

    # ---- compact stdout summary (the only thing meant for model context) ----
    print("== extract-shaders summary ==")
    print(f"scanned: {len(readable)} file(s), {total_bytes} bytes, "
          f"{total_literals} string literals")
    print(f"shaders extracted: {len(index)} "
          f"({', '.join(f'{v} {k}' for k, v in sorted(kinds.items()))})")
    if all_uniforms:
        tops = sorted(all_uniforms.items(), key=lambda kv: -kv[1])[:20]
        print(f"uniforms seen: {', '.join(n for n, _ in tops)}"
              + (" ..." if len(all_uniforms) > 20 else ""))
    if all_varyings:
        print(f"varyings seen: {', '.join(sorted(all_varyings)[:15])}")
    if all_templates:
        print("template injections ${...}: "
              + ", ".join(f"${{{n}}} x{c}" for n, c in sorted(all_templates.items())))
    if tsl_hits:
        print(f"TSL signals (JS-side, see references/tsl-extraction.md): "
              + ", ".join(f"{s} x{c}" for s, c in sorted(tsl_hits.items())))
    print(f"files written to {ns.out}/:")
    for e in index:
        preview = " ".join(e["content"][: ns.preview].split())
        print(f"  {e['file']:48s} {e['chars']:6d} chars  | {preview}")
    print("next: read the smallest fragment shader file first; "
          "grep the bundle for targeted context only — never read the whole bundle.")

    # machine-readable sidecar
    meta = {
        "files": readable,
        "min_score": ns.min_score,
        "shaders": [{k: v for k, v in e.items() if k != "content"} for e in index],
        "uniforms": sorted(all_uniforms),
        "varyings": sorted(all_varyings),
        "templates": sorted(all_templates),
        "tsl_signals": tsl_hits,
    }
    with open(os.path.join(ns.out, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    sys.exit(0)


if __name__ == "__main__":
    main()
