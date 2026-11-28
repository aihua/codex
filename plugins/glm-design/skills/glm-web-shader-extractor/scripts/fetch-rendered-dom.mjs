#!/usr/bin/env node
/**
 * fetch-rendered-dom.mjs — capture the JS-rendered DOM and WebGL metadata
 *
 * Usage:
 *   node fetch-rendered-dom.mjs <URL> [outDir] [--swiftshader]
 *
 * Playwright resolution order (first hit wins):
 *   1. a globally importable 'playwright' (NODE_PATH / global install)
 *   2. the persistent cache dir ~/.cache/playwright-runner/
 *   3. auto-install into the cache dir — pnpm first, npm as fallback
 *      (matches package-manager preference of the host)
 *
 * Output files in outDir (default /tmp/rendered):
 *   dom.html          — fully rendered HTML
 *   canvas-info.json  — every <canvas> element's metadata
 *   webgl-info.json   — first canvas WebGL context hints
 *   console.log       — page console output
 *   screenshot.png    — viewport screenshot
 *   network.json      — runtime-loaded JS / wasm / glsl resources
 *
 * --swiftshader launches Chromium with software GL (use when the host has
 * no GPU, the screenshot is black, or WebGL context creation fails).
 */

import { execSync } from 'child_process';
import { existsSync, writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';

const args = process.argv.slice(2);
const url = args.find(a => !a.startsWith('--'));
const outDir = args.find(a => !a.startsWith('--') && a !== url) || '/tmp/rendered';
const swiftshader = args.includes('--swiftshader');

if (!url) {
  console.error('Usage: node fetch-rendered-dom.mjs <URL> [outDir] [--swiftshader]');
  process.exit(1);
}

// --- resolve playwright -----------------------------------------------------
const runnerDir = join(homedir(), '.cache', 'playwright-runner');
const pwDir = join(runnerDir, 'node_modules', 'playwright');
const chromiumMarker = join(runnerDir, '.chromium-installed');

function havePnpm() {
  try { execSync('command -v pnpm >/dev/null 2>&1', { shell: '/bin/sh' }); return true; }
  catch { return false; }
}

async function loadPlaywright() {
  // 1. globally importable playwright
  try {
    return await import('playwright');
  } catch { /* not globally resolvable */ }

  // 2. cached install
  if (existsSync(pwDir)) {
    return await import(join(pwDir, 'index.mjs'));
  }

  // 3. auto-install into the cache dir (pnpm first, npm fallback)
  console.log('Installing playwright (one-time setup, cache dir)...');
  mkdirSync(runnerDir, { recursive: true });
  writeFileSync(join(runnerDir, 'package.json'), '{"type":"module","private":true}');
  const installed = (() => {
    if (havePnpm()) {
      try {
        execSync('pnpm add playwright', { cwd: runnerDir, stdio: 'inherit' });
        return true;
      } catch {
        console.log('pnpm add failed, retrying with mirror registry...');
        try {
          execSync('pnpm add playwright --registry=https://registry.npmmirror.com', { cwd: runnerDir, stdio: 'inherit' });
          return true;
        } catch { return false; }
      }
    }
    return false;
  })();
  if (!installed) {
    try {
      execSync('npm install playwright', { cwd: runnerDir, stdio: 'inherit' });
    } catch {
      console.log('npm install failed, retrying with registry mirror...');
      execSync('npm install playwright --registry=https://registry.npmmirror.com', { cwd: runnerDir, stdio: 'inherit' });
    }
  }

  if (!existsSync(pwDir)) {
    console.error('playwright package still not importable after install — giving up.');
    process.exit(1);
  }
  return await import(join(pwDir, 'index.mjs'));
}

async function ensureChromium() {
  // browser binaries live in ~/.cache/ms-playwright and are shared across
  // installs of the same version. Only install once per cache dir.
  // First: ask playwright itself whether its chromium already exists
  // (globally importable playwright usually ships or has installed it).
  try {
    const p = chromium.executablePath();
    if (p && existsSync(p)) {
      mkdirSync(runnerDir, { recursive: true });
      writeFileSync(chromiumMarker, new Date().toISOString());
      return;
    }
  } catch { /* not downloadable/installed — fall through */ }
  if (existsSync(chromiumMarker)) return;
  console.log('Installing chromium browser...');
  const tries = [];
  if (existsSync(join(runnerDir, 'node_modules', '.bin', 'playwright'))) {
    tries.push('node_modules/.bin/playwright install chromium');
  }
  tries.push('playwright install chromium');   // a global playwright CLI, if present
  tries.push('npx playwright install chromium');
  let done = false;
  for (const cmd of tries) {
    try {
      execSync(cmd, { cwd: runnerDir, stdio: 'inherit' });
      done = true; break;
    } catch { /* try next */ }
  }
  if (!done) {
    console.log('Chromium download failed, retrying with mirror...');
    const fallback = havePnpm() ? 'pnx playwright install chromium' : 'npx playwright install chromium';
    try {
      execSync(`PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright ${fallback}`,
        { cwd: runnerDir, stdio: 'inherit', shell: '/bin/sh' });
      done = true;
    } catch { /* leave marker unwritten to retry next run */ }
  }
  if (done) writeFileSync(chromiumMarker, new Date().toISOString());
  else console.error('Chromium could not be installed — try PLAYWRIGHT_DOWNLOAD_HOST manually.');
}

const pw = await loadPlaywright();
const { chromium } = pw;
await ensureChromium();

// --- capture ----------------------------------------------------------------
mkdirSync(outDir, { recursive: true });

const consoleLogs = [];
const networkRequests = [];

const launchArgs = swiftshader
  ? ['--use-angle=swiftshader', '--use-gl=angle', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
  : [];
if (swiftshader) console.log('SwiftShader software GL enabled (--swiftshader).');

let browser = null;
try {
  browser = await chromium.launch({ headless: true, args: launchArgs });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 2,
  });
  const page = await context.newPage();

  page.on('console', msg => {
    consoleLogs.push(`[${msg.type()}] ${msg.text()}`);
  });

  page.on('response', response => {
    const reqUrl = response.url();
    const type = response.headers()['content-type'] || '';
    if (/\.(js|mjs|wasm|bin|glsl|frag|vert|svg)(\?|$)/.test(reqUrl) || type.includes('javascript')) {
      networkRequests.push({
        url: reqUrl,
        status: response.status(),
        type: type.split(';')[0],
        size: parseInt(response.headers()['content-length'] || '0'),
      });
    }
  });

  console.log(`Navigating to ${url} ...`);
  // networkidle is strict on asset-heavy pages — degrade gracefully
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
  } catch {
    console.log('networkidle timeout — retrying with waitUntil "load"...');
    try {
      await page.goto(url, { waitUntil: 'load', timeout: 15000 });
    } catch {
      console.log('"load" timeout too — retrying with "domcontentloaded"...');
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
    }
  }

  // give WebGL scenes time to initialise
  await page.waitForTimeout(3000);

  // 1. full rendered DOM
  const html = await page.content();
  writeFileSync(join(outDir, 'dom.html'), html);
  console.log(`dom.html — ${html.length} bytes`);

  // 2. canvas info
  const canvasInfo = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('canvas')).map((c, i) => ({
      index: i,
      outerHTML: c.outerHTML.slice(0, 500),
      width: c.width,
      height: c.height,
      clientWidth: c.clientWidth,
      clientHeight: c.clientHeight,
      dataEngine: c.dataset.engine || null,
      dataRenderer: c.dataset.renderer || null,
      id: c.id || null,
      className: c.className || null,
      parentTag: c.parentElement?.tagName || null,
      parentClass: c.parentElement?.className?.slice(0, 100) || null,
    }));
  });
  writeFileSync(join(outDir, 'canvas-info.json'), JSON.stringify(canvasInfo, null, 2));
  console.log(`canvas-info.json — ${canvasInfo.length} canvas(es) found`);

  // 3. WebGL info (report only; never create a second context)
  const webglInfo = await page.evaluate(() => {
    const canvas = document.querySelector('canvas');
    if (!canvas) return { error: 'no canvas found' };
    return {
      found: true,
      width: canvas.width,
      height: canvas.height,
      dataEngine: canvas.dataset.engine || null,
      dataRenderer: canvas.dataset.renderer || null,
    };
  });
  writeFileSync(join(outDir, 'webgl-info.json'), JSON.stringify(webglInfo, null, 2));
  console.log(`webgl-info.json — ${JSON.stringify(webglInfo).slice(0, 100)}`);

  // 4. console logs
  writeFileSync(join(outDir, 'console.log'), consoleLogs.join('\n'));
  console.log(`console.log — ${consoleLogs.length} entries`);

  // 5. screenshot
  await page.screenshot({ path: join(outDir, 'screenshot.png'), fullPage: false });
  console.log('screenshot.png — saved');

  // 6. network requests
  writeFileSync(join(outDir, 'network.json'), JSON.stringify(networkRequests, null, 2));
  console.log(`network.json — ${networkRequests.length} JS/resource requests captured`);

  await browser.close();
  console.log(`\nDone. Files saved to ${outDir}`);
} catch (err) {
  // one line of cause + actionable next steps; keep exit-code discipline (1)
  console.error(`fetch failed: ${err && err.message ? err.message : err}`);
  console.error('Retry with --swiftshader if this looks GPU/WebGL related; otherwise fall back to curl-only mode (references/fallback.md).');
  if (browser) { try { await browser.close(); } catch { /* already closed */ } }
  process.exit(1);
}
