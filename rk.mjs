// env: CFG=reel2 CTA=ig|url OUT=dir FROM TO PORT ONLY=t1,t2
// Headless-Chrome frame grabber. Each run gets its own Chrome profile (.chrome-<port>-<pid>) that is deleted when the
// run ends, on success, on error, and on Ctrl+C (rkclean.mjs). Profiles older than a day are swept at start.
import { spawn } from 'node:child_process'
import { mkdirSync, writeFileSync } from 'node:fs'
import { pathToFileURL } from 'node:url'
import path from 'node:path'
import { chromeProfile, sweepStale } from './rkclean.mjs'
const dir = path.dirname(new URL(import.meta.url).pathname.replace(/^\/(\w:)/, '$1'))
const E = process.env, port = Number(E.PORT ?? 9350), out = path.join(dir, E.OUT)
sweepStale()
mkdirSync(out, { recursive: true })
const profile = chromeProfile('.chrome', port)
const chrome = spawn(E.CHROME ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe', ['--headless=new', `--remote-debugging-port=${port}`, '--hide-scrollbars', '--allow-file-access-from-files', `--user-data-dir=${profile.dir}`, '--window-size=1080,1920', 'about:blank'], { stdio: 'ignore' })
profile.attach(chrome)
let ws
try {
  let targets
  for (let i = 0; i < 50; i++) { try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); if (targets.some(t => t.type === 'page')) break } catch {} await new Promise(r => setTimeout(r, 200)) }
  if (!targets?.some(t => t.type === 'page')) throw new Error(`Chrome on port ${port} never came up`)
  ws = new WebSocket(targets.find(t => t.type === 'page').webSocketDebuggerUrl)
  await new Promise((r, j) => { ws.addEventListener('open', r); ws.addEventListener('error', () => j(new Error('devtools socket failed'))) })
  let id = 0; const wait = new Map()
  ws.addEventListener('message', ev => { const m = JSON.parse(ev.data); if (m.id && wait.has(m.id)) { wait.get(m.id).ok(m); wait.delete(m.id) } })
  // if Chrome dies mid-run, fail the pending calls instead of hanging forever
  chrome.once('exit', () => { for (const w of wait.values()) w.fail(new Error('Chrome exited')); wait.clear() })
  // a call that never answers (frozen renderer) fails after 30 s instead of hanging the whole render
  const send = (method, params = {}) => new Promise((ok, fail) => {
    const i = ++id, timer = setTimeout(() => { wait.delete(i); fail(new Error(`${method} timed out (30 s)`)) }, 30000)
    wait.set(i, { ok: m => { clearTimeout(timer); ok(m) }, fail: e => { clearTimeout(timer); fail(e) } })
    ws.send(JSON.stringify({ id: i, method, params }))
  })
  const ev = async x => { const r = await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true }); if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails)); return r.result?.result?.value }
  await send('Emulation.setDeviceMetricsOverride', { width: 1080, height: 1920, deviceScaleFactor: 1, mobile: false })
  if (E.TRANSPARENT) await send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } }) // overlays with alpha
  await send('Page.navigate', { url: pathToFileURL(path.join(dir, E.HTML ?? 'reelkit.html')).href + `?cfg=${E.CFG}&cta=${E.CTA ?? 'ig'}` })
  let ready = false
  for (let i = 0; i < 600 && !ready; i++) { ready = await ev('window.READY === true').catch(() => false); if (!ready) await new Promise(r => setTimeout(r, 100)) }
  if (!ready) throw new Error("page never became ready (60 s)")
  await ev('document.fonts.ready.then(() => 1)')
  if (E.HTML) console.log('layout:', JSON.stringify(await ev('window.LAYOUT')))
  if (E.EVENTS) writeFileSync(E.EVENTS, JSON.stringify(await ev('window.EVENTS || []'))) // sound-effect cues for sfx.py
  const dur = await ev('window.DURATION')
  const total = Math.round(dur * 30)
  const only = E.ONLY?.split(',').map(Number)
  const idx = only ? only.map(t => Math.round(t * 30)) : Array.from({ length: total }, (_, i) => i).slice(Number(E.FROM ?? 0), Number(E.TO ?? total))
  for (const i of idx) {
    await ev(`render(${i / 30})`)
    const shot = await send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: 1080, height: 1920, scale: 1 } })
    writeFileSync(path.join(out, only ? `t${(i / 30).toFixed(2)}.png` : `${String(i + 1).padStart(5, '0')}.png`), Buffer.from(shot.result.data, 'base64'))
  }
  console.log('done', E.CFG, idx.length, 'of', total)
} catch (e) {
  console.error('rk:', e.message); process.exitCode = 1
} finally {
  try { ws?.close() } catch {}
  await profile.cleanup(chrome)
}
