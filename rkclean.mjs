// Temp-folder housekeeping for reelkit (frame dumps and headless-Chrome profiles).
//   node rkclean.mjs frames <dir>... [--require <file.mp4>]   delete frame folders, only if the finished .mp4 exists and isn't empty
//   node rkclean.mjs stale                                    delete .chrome-* profiles older than a day (skips ones still in use)
// rk.mjs and capture-docs.mjs import chromeProfile() / sweepStale() from here.
import { existsSync, readdirSync, rmSync, statSync } from 'node:fs'
import path from 'node:path'

export const DIR = path.dirname(new URL(import.meta.url).pathname.replace(/^\/(\w:)/, '$1'))
const DAY = 24 * 3600 * 1000
// only names reelkit itself creates: <prefix>-<anything>, the layout-check stills and the per-run Chrome profiles
const FRAME_DIR = /^(?:(?:fd|fb|fq|qz|gr|hw|V|P)-[\w.-]+|fr\d+u?)$/   // fd-x-123456, fd-pre, qz-test, V-en, P-aws-u, fr2, fr2u
const PROFILE_DIR = /^\.chrome(-[\w.]+)*$/

function inside(name) {
  const p = path.resolve(DIR, name)
  return path.dirname(p) === path.resolve(DIR) ? p : null           // direct children of reelkit only
}

// Windows can hold freshly written files for a moment (antivirus scan, Chrome exiting): retry for up to ~10 s
function remove(p, quiet = false) {
  let err
  for (let attempt = 0; attempt < 4; attempt++) {
    try { rmSync(p, { recursive: true, force: true, maxRetries: 10, retryDelay: 250 }) } catch (e) { err = e }
    if (!existsSync(p)) return true
    const t = Date.now(); while (Date.now() - t < 500) { /* wait for the lock to clear */ }
  }
  if (!quiet) console.error(`rkclean: could not remove ${path.basename(p)}: ${err?.code ?? 'still present'}`)
  return false
}

/** A Chrome profile that belongs to this one process. Call cleanup(chrome) when done: kills Chrome, waits for it, deletes the folder. */
export function chromeProfile(prefix, port) {
  const dir = path.join(DIR, `${prefix}-${port}-${process.pid}`)
  let done = false
  const cleanup = async chrome => {
    if (done) return; done = true
    if (chrome && chrome.exitCode === null) {
      const exited = new Promise(r => chrome.once('exit', r))
      chrome.kill()
      await Promise.race([exited, new Promise(r => setTimeout(r, 5000))])
    }
    remove(dir)                                                       // retries cover Windows releasing file locks late
  }
  // Ctrl+C or a kill: Chrome must die before its folder can go
  const onSignal = sig => { try { cleanupSync() } finally { process.exit(sig === 'SIGINT' ? 130 : 143) } }
  let proc = null
  const cleanupSync = () => { if (done) return; done = true; try { proc?.kill() } catch {} ; const t = Date.now(); while (Date.now() - t < 1500) { /* let Chrome exit */ } remove(dir) }
  process.once('SIGINT', onSignal); process.once('SIGTERM', onSignal)
  process.once('exit', cleanupSync)                                   // last resort if something exits without the finally
  return { dir, cleanup, attach: chrome => { proc = chrome } }
}

/** Delete .chrome-* profiles older than a day. One that is still in use fails to delete and is left alone. */
export function sweepStale(maxAge = DAY) {
  let n = 0
  for (const name of readdirSync(DIR)) {
    if (!PROFILE_DIR.test(name)) continue
    const p = inside(name)
    try { if (!p || !statSync(p).isDirectory() || Date.now() - statSync(p).mtimeMs < maxAge) continue } catch { continue }
    if (remove(p, true)) n++
  }
  return n
}

/** Delete frame folders after a successful export. */
export function removeFrames(names, requireFile) {
  if (requireFile) {
    let ok = false
    try { ok = statSync(requireFile).size > 0 } catch {}
    if (!ok) { console.error(`rkclean: ${requireFile} missing or empty, keeping frames`); return 0 }
  }
  let n = 0
  for (const name of names) {
    const p = FRAME_DIR.test(name) ? inside(name) : null
    if (!p) { console.error(`rkclean: refusing ${name} (not a reelkit frame folder)`); continue }
    if (existsSync(p) && remove(p)) n++
  }
  return n
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(DIR, 'rkclean.mjs')) {
  const [cmd, ...rest] = process.argv.slice(2)
  if (cmd === 'stale') console.log(`rkclean: removed ${sweepStale()} stale Chrome profile(s)`)
  else if (cmd === 'frames') {
    const i = rest.indexOf('--require'), req = i >= 0 ? rest[i + 1] : null
    const names = i < 0 ? rest : rest.filter((_, k) => k !== i && k !== i + 1)
    console.log(`rkclean: removed ${removeFrames(names, req)} frame folder(s)`)
  } else { console.error('usage: node rkclean.mjs frames <dir>... [--require file.mp4] | stale'); process.exit(2) }
}
