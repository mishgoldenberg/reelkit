// The talking robot as a reusable piece (robot.html shows it alone, mag.html puts it under the content).
// Whole 3D poses (character/blank-<pose>.png, face screen empty) switch with a quick pop; every pose is placed so its face
// screen lands on (fx, fy) at width sw, so the head stays put while the arms change. The face is drawn live on the screen:
// blinks, glances toward the hand it points with, an expression per pose, and a mouth that follows the voice loudness.
//   const bot = await Robot(hostDiv, { fx, fy, sw })     then every frame: bot.render(t, loudness, talking, cues)
//   cues = [{ t, pose }, ...] sorted by time
;(function () {
  const POSES = {   // pose -> face expression, and where the eyes look
    'talk-open': ['happy', 0, 0], explain: ['happy', 0, 0], present: ['neutral', 1, 0], count: ['neutral', -1, -.4],
    'point-up': ['neutral', 0, -1], 'point-up-left': ['neutral', -1, -1], 'point-up-right': ['neutral', 1, -1],
    'thumbs-up': ['happy', 0, 0], wave: ['happy', 0, 0], wow: ['wow', 0, 0], shocked: ['wow', 0, 0],
    skeptical: ['skeptical', .6, -.3], crossed: ['skeptical', 0, 0], shrug: ['neutral', 0, 0] }
  const FLAT = ['explain', 'count', 'crossed', 'shocked', 'present', 'shrug']   // front-facing sheet poses: screen is level
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x)), p = (t, a, b) => clamp((t - a) / (b - a))
  let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647
  const BLINKS = []; for (let t = 1.2; t < 300; t += 2.2 + rnd() * 2.2) BLINKS.push(t)

  window.ROBOT_POSES = Object.keys(POSES)
  window.Robot = async function (host, { fx, fy, sw, base = '' }) {
    let meta; try { meta = await (await fetch(base + 'character/blank.json')).json() } catch { return { render() {} } }   // no character yet: no robot
    host.style.transformOrigin = `${fx}px ${fy + sw * 2}px`
    const NS = 'http://www.w3.org/2000/svg'
    const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('width', 1080); svg.setAttribute('height', 1920)
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;z-index:5'
    svg.innerHTML = `<g class="rb-fg"><g style="filter:drop-shadow(0 0 4px rgba(255,243,223,.9)) drop-shadow(0 0 12px rgba(255,190,120,.7))">
      <g class="rb-eyes"></g><path class="rb-mouth" fill="none" stroke="#fff3df" stroke-linecap="round" stroke-linejoin="round"/></g></g>`
    const S = {}
    for (const n in POSES) {
      const m = meta[n], el = document.createElement('img'); el.src = base + `character/blank-${n}.png`
      const k = sw / m.w; el.style.cssText = `position:absolute;left:0;top:0;opacity:0;transform-origin:0 0;transform:translate(${fx - m.cx * k}px,${fy - m.cy * k}px) scale(${k})`
      host.appendChild(el); S[n] = { el, ang: FLAT.includes(n) ? 0 : m.ang }
    }
    host.appendChild(svg)
    await Promise.all(Object.values(S).map(s => s.el.complete ? 1 : new Promise(r => { s.el.onload = r; s.el.onerror = r })))
    const fg = svg.querySelector('.rb-fg'), eyesG = svg.querySelector('.rb-eyes'), mouth = svg.querySelector('.rb-mouth')

    function face(t, P, a, talking) {                                 // drawn around (0,0) = screen centre, 230 px wide
      const [expr, gx, gy] = POSES[P]
      const bl = BLINKS.find(x => t >= x && t < x + .16), o = bl === undefined ? 1 : Math.abs((t - bl) / .08 - 1)
      const lx = gx * 9 + Math.sin(t * .7) * 2, ly = gy * 7, ey = -18, my = 36, sw = 7.5, st = `fill="none" stroke="#fff3df" stroke-width="${sw}" stroke-linecap="round"`
      const eye = (x, i) => {
        if (expr === 'happy') return `<path ${st} d="M${x - 22},${ey + 6} Q${x},${ey - 30 * Math.max(o, .15)} ${x + 22},${ey + 6}"/>`
        if (expr === 'skeptical' && i === 0) return `<path ${st} d="M${x - 22},${ey - 6} L${x + 22},${ey + 2}"/><path ${st} d="M${x - 20},${ey + 12} Q${x},${ey + 12 - 8 * o} ${x + 20},${ey + 12}"/>`
        const R = expr === 'wow' ? 1.25 : 1
        return `<ellipse fill="#fff3df" cx="${x}" cy="${ey}" rx="${19 * R}" ry="${22 * R * Math.max(o, .08)}"/>` + (o > .4 ? `<circle cx="${x + lx}" cy="${ey + ly}" r="${8 * R}" fill="#e2601c"/>` : '')
      }
      eyesG.innerHTML = [-44, 44].map(eye).join('')
      const op = talking ? a * 30 : 0, w = 30 - a * 6
      let d
      if (op >= 3) d = `M${-w},${my - 6} Q0,${my - 2} ${w},${my - 6} Q${w * .8},${my + 4 + op} 0,${my + 6 + op} Q${-w * .8},${my + 4 + op} ${-w},${my - 6} Z`
      else if (expr === 'wow') d = `M-12,${my} a12,14 0 1,0 24,0 a12,14 0 1,0 -24,0`
      else if (expr === 'skeptical') d = `M-24,${my + 2} Q0,${my - 4} 24,${my - 6}`
      else if (expr === 'neutral') d = `M-22,${my} Q0,${my + 10} 22,${my}`
      else d = `M-30,${my - 4} Q0,${my + 18} 30,${my - 4}`
      mouth.setAttribute('d', d); mouth.setAttribute('stroke-width', sw); mouth.setAttribute('fill', op >= 3 ? '#7a2a0c' : 'none')
    }
    return {
      render(t, a, talking, cues, enterAt = 0) {
        let ci = 0; while (ci + 1 < cues.length && t >= cues[ci + 1].t) ci++
        const cur = cues[ci].pose, prev = ci ? cues[ci - 1].pose : cur, since = t - cues[ci].t, mix = ci ? p(since, 0, .12) : 1
        const pop = ci ? 1 + .045 * Math.exp(-since * 9) * Math.cos(since * 22) : 1
        for (const n in S) S[n].el.style.opacity = n === cur ? mix : n === prev && mix < 1 ? 1 - mix : 0
        const enter = 1 - Math.pow(1 - p(t, enterAt, enterAt + .5), 3)
        const bob = Math.sin(t * 2.1) * 6 + a * 5 + (1 - enter) * 1100, sway = Math.sin(t * .9) * 1.2 + (talking ? Math.sin(t * 4.7) * a * 1.2 : 0)
        const br = 1 + Math.sin(t * 2.1 + 1) * .007
        host.style.transform = `translateY(${bob}px) rotate(${sway}deg) scale(${pop},${pop * br})`
        fg.setAttribute('transform', `translate(${fx},${fy}) rotate(${S[prev].ang + (S[cur].ang - S[prev].ang) * mix}) scale(${sw / 230})`)
        face(t, mix < .5 ? prev : cur, a, talking)
      }
    }
  }
})()
