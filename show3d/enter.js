// World for show3d.html ?cfg=enter: "what happens when you press Enter". Laptop (modelled), DNS kiosk with a hologram,
// server rack, the scanned parcel travelling the routes, TCP pulses, TLS padlock. See show3d.html for the shared shell.
export default async function ({ THREE, scene, V, clamp, p, ease, inout, back, hash, canvasTex, label, parcel, drawTag, makeRack, RoundedBoxGeometry, CYAN, GREEN }) {
// ---------- laptop (modelled): space-grey aluminium, real keyboard, hinged lid, live screen ----------
const LAP = V(-1.3, 0, 3.4)
const alu = new THREE.MeshStandardMaterial({ color: 0x3b4048, metalness: .9, roughness: .32 })
const laptop = new THREE.Group(); laptop.position.copy(LAP); laptop.rotation.y = .42; scene.add(laptop)
const base = new THREE.Mesh(new RoundedBoxGeometry(3.0, .12, 2.05, 4, .05), alu); base.position.y = .06; base.castShadow = base.receiveShadow = true; laptop.add(base)
const deck = new THREE.Mesh(new THREE.PlaneGeometry(2.7, 1.05), new THREE.MeshStandardMaterial({ color: 0x15181d, roughness: .7 }))
deck.rotation.x = -Math.PI / 2; deck.position.set(0, .121, -.35); laptop.add(deck)
const keyMat = new THREE.MeshStandardMaterial({ color: 0x0d0f12, roughness: .55, metalness: .1 })
const keyGeo = new RoundedBoxGeometry(.165, .04, .155, 2, .02)
const keys = new THREE.InstancedMesh(keyGeo, keyMat, 14 * 5); let ki = 0; const m4 = new THREE.Matrix4()
for (let r = 0; r < 5; r++) for (let c = 0; c < 14; c++) {
  if (r >= 1 && r <= 2 && c === 13) continue                                                      // room for the big Enter key
  m4.makeTranslation(-1.2 + c * .185, .14, -.75 + r * .19); keys.setMatrixAt(ki++, m4)
}
keys.count = ki; keys.castShadow = true; laptop.add(keys)
const ENTER_LOCAL = V(-1.2 + 13 * .185, .14, -.75 + 1.5 * .19)
const enterKey = new THREE.Mesh(new RoundedBoxGeometry(.2, .045, .35, 3, .02), new THREE.MeshStandardMaterial({ color: 0x0d0f12, roughness: .5, emissive: CYAN, emissiveIntensity: 0 }))
enterKey.position.copy(ENTER_LOCAL); laptop.add(enterKey)
const enterGlyph = (() => { const { g, t } = canvasTex(128, 256); g.strokeStyle = '#3ee6ff'; g.lineWidth = 14; g.lineCap = 'round'; g.beginPath(); g.moveTo(84, 60); g.lineTo(84, 170); g.lineTo(36, 170); g.stroke(); g.beginPath(); g.moveTo(56, 146); g.lineTo(32, 170); g.lineTo(56, 194); g.stroke(); return t })()
const glyph = new THREE.Mesh(new THREE.PlaneGeometry(.16, .32), new THREE.MeshBasicMaterial({ map: enterGlyph, transparent: true, toneMapped: false }))
glyph.rotation.x = -Math.PI / 2; glyph.position.y = .024; enterKey.add(glyph)
const pad = new THREE.Mesh(new THREE.PlaneGeometry(1.1, .62), new THREE.MeshStandardMaterial({ color: 0x2c3036, roughness: .4, metalness: .6 }))
pad.rotation.x = -Math.PI / 2; pad.position.set(0, .122, .55); laptop.add(pad)
const hinge = new THREE.Group(); hinge.position.set(0, .12, -1.0); hinge.rotation.x = -.2; laptop.add(hinge)
const lid = new THREE.Mesh(new RoundedBoxGeometry(3.0, 1.95, .06, 4, .03), alu); lid.position.set(0, .975, 0); lid.castShadow = true; hinge.add(lid)
const scr = canvasTex(1024, 640)
const screen = new THREE.Mesh(new THREE.PlaneGeometry(2.8, 1.75), new THREE.MeshBasicMaterial({ map: scr.t, toneMapped: false }))
screen.position.set(0, .975, .032); hinge.add(screen)
const lapLabel = label('YOU', '#e9f1f7', .28); lapLabel.position.set(0, 2.5, -1); laptop.add(lapLabel)

function drawScreen(mode, k) {                                                                     // the browser on the laptop
  const g = scr.g; g.fillStyle = '#121d2a'; g.fillRect(0, 0, 1024, 640)
  g.fillStyle = '#131c27'; g.fillRect(0, 0, 1024, 70)
  ;['#ff6159', '#ffbd2e', '#28c941'].forEach((c, i) => { g.fillStyle = c; g.beginPath(); g.arc(34 + i * 30, 35, 9, 0, 7); g.fill() })
  g.fillStyle = '#0a1018'; g.beginPath(); g.roundRect(150, 16, 720, 40, 12); g.fill()
  g.font = "600 24px 'JetBrains Mono'"; g.fillStyle = '#e9f1f7'; g.textBaseline = 'middle'; g.fillText('google.com', 176, 37)
  if (mode === 'type') { if (Math.floor(k * 4) % 2 === 0) { g.fillStyle = '#3ee6ff'; g.fillRect(330, 24, 3, 26) } }
  if (mode === 'load') { g.fillStyle = '#3ee6ff'; g.fillRect(0, 68, 1024 * k, 4) }
  if (mode === 'page') {
    const B = [[262, 170, 500, 70, '#3ee6ff'], [212, 290, 600, 60, '#24344a'], [312, 390, 180, 50, '#7dffa8'], [532, 390, 180, 50, '#24344a'], [162, 490, 700, 18, '#1b2736'], [162, 530, 560, 18, '#1b2736']]
    B.forEach(([x, y, w, h, c], i) => { const kk = back(p(k, .05 + i * .11, .25 + i * .11)); if (kk <= 0) return
      g.globalAlpha = clamp(kk * 2); g.fillStyle = c; g.beginPath(); g.roundRect(x + w / 2 - w * kk / 2, y, w * kk, h, 12); g.fill(); g.globalAlpha = 1 })
  }
  scr.t.needsUpdate = true
}

// ---------- server rack (modelled): 8 units, drive bays, blinking LEDs ----------
const SRV = V(-1.0, 0, -4.8)
const { rack, leds, dark } = makeRack(SRV, .3, 'SERVER')
// ---------- DNS kiosk: pedestal + hologram card ----------
const DNS = V(1.9, 0, -.6)
const ped = new THREE.Mesh(new THREE.CylinderGeometry(.55, .7, 1.2, 48), dark); ped.position.set(DNS.x, .6, DNS.z); ped.castShadow = true; scene.add(ped)
const ring = new THREE.Mesh(new THREE.TorusGeometry(.62, .025, 12, 64), new THREE.MeshBasicMaterial({ color: CYAN, toneMapped: false })); ring.rotation.x = Math.PI / 2; ring.position.set(DNS.x, 1.21, DNS.z); scene.add(ring)
const holo = canvasTex(1024, 512)
const holoCard = new THREE.Mesh(new THREE.PlaneGeometry(3.0, 1.5), new THREE.MeshBasicMaterial({ map: holo.t, transparent: true, toneMapped: false, depthWrite: false, side: THREE.DoubleSide }))
holoCard.position.set(DNS.x, 3.3, DNS.z); scene.add(holoCard)
const dnsLabel = label('DNS', '#3ee6ff', .28); dnsLabel.position.set(DNS.x, 1.75, DNS.z + .9); scene.add(dnsLabel)
function drawHolo(k, s) {
  const g = holo.g; g.clearRect(0, 0, 1024, 512)
  g.globalAlpha = k; g.fillStyle = 'rgba(62,230,255,.10)'; g.strokeStyle = 'rgba(62,230,255,.9)'; g.lineWidth = 6; g.beginPath(); g.roundRect(8, 8, 1008, 496, 36); g.fill(); g.stroke()
  g.font = "700 40px 'JetBrains Mono'"; g.fillStyle = 'rgba(62,230,255,.8)'; g.textBaseline = 'middle'; g.fillText('DNS · WHERE IS', 60, 90)
  g.font = "800 84px 'JetBrains Mono'"; g.fillStyle = '#e9f1f7'; g.fillText('google.com' + (s < 2.3 ? (Math.floor(s * 3) % 2 ? ' ?' : '') : ' ✓'), 60, 200)
  const ip = '142.250.75.14', n = Math.floor(clamp((s - 2.4) / .6) * ip.length)
  if (n > 0) { g.fillStyle = '#7dffa8'; g.font = "800 84px 'JetBrains Mono'"; g.fillText('→ ' + ip.slice(0, n), 60, 360) }
  g.globalAlpha = 1; holo.t.needsUpdate = true
}

// ---------- routes: laptop -> DNS -> server, and the direct line back ----------
laptop.updateMatrixWorld(true); rack.updateMatrixWorld(true)
const SCR = laptop.localToWorld(V(0, 1.35, .25)), DTOP = V(DNS.x, 2.1, DNS.z), SFRONT = rack.localToWorld(V(0, 2.4, 1.95))   // parcels appear/vanish in open air
const mid = (a, b, h) => a.clone().lerp(b, .5).add(V(0, h, 0))
const A = new THREE.CatmullRomCurve3([SCR, SCR.clone().lerp(DTOP, .35).add(V(0, 1.4, 0)), DTOP.clone().lerp(SCR, .25).add(V(0, .9, 0)), DTOP])
const B = new THREE.CatmullRomCurve3([DTOP, DTOP.clone().lerp(SFRONT, .3).add(V(0, 1.2, 0)), SFRONT.clone().lerp(DTOP, .3).add(V(0, 1.0, 0)), SFRONT])
const R = new THREE.CatmullRomCurve3([SFRONT, mid(SFRONT, SCR, 2.6).add(V(-2.0, 0, 0)), SCR.clone().add(V(0, 1.5, .9)), SCR])   // comes down onto the laptop from above, never through the lid
const tubeMat = (c, o) => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: o, toneMapped: false, depthWrite: false })
const tubes = [[A, CYAN, .35], [B, CYAN, .35], [R, GREEN, .5]].map(([cv, c, o]) => { const m = new THREE.Mesh(new THREE.TubeGeometry(cv, 200, .018, 8), tubeMat(c, o)); scene.add(m); return m })
const backTube = tubes[2]   // the direct line is only shown while something uses it (handshake, the answer)

// ---------- the parcel (scanned CC0 cardboard box) with an address label ----------
const req = parcel('#3ee6ff'), res = parcel('#7dffa8')
const resGlow = new THREE.PointLight(GREEN, 6, 3, 2); res.add(resGlow)
drawTag(res, 'RESPONSE', '200 OK')
// padlock that clamps onto the parcel (TLS)
const lockMat = new THREE.MeshStandardMaterial({ color: 0x9fe9ff, metalness: 1, roughness: .2, emissive: CYAN, emissiveIntensity: .25 })
const lock = new THREE.Group(); const lb = new THREE.Mesh(new RoundedBoxGeometry(.34, .28, .12, 3, .04), lockMat)
const sh = new THREE.Mesh(new THREE.TorusGeometry(.11, .028, 12, 32, Math.PI), lockMat); sh.position.y = .14
lock.add(lb, sh); req.add(lock)
const shield = new THREE.Mesh(new THREE.IcosahedronGeometry(.75, 1), new THREE.MeshBasicMaterial({ color: CYAN, wireframe: true, transparent: true, opacity: .0, toneMapped: false })); req.add(shield)
// handshake pulses
const pulses = ['SYN', 'SYN-ACK', 'ACK'].map((n, i) => {
  const o = new THREE.Mesh(new THREE.SphereGeometry(.13, 24, 16), new THREE.MeshBasicMaterial({ color: i === 1 ? GREEN : CYAN, toneMapped: false }))
  const l = label(n, i === 1 ? '#7dffa8' : '#3ee6ff', .26); scene.add(o, l); return { o, l, i }
})
const keyLight = new THREE.PointLight(CYAN, 0, 2.5, 2); laptop.add(keyLight); keyLight.position.copy(ENTER_LOCAL).add(V(0, .25, 0))
const wp = v => laptop.localToWorld(v.clone())
const ENTER = wp(ENTER_LOCAL)

// camera pose for scene `n` at s seconds into it: [position, target]
function shot(n, s, d) {
  const L = (x, y, z) => LAP.clone().add(V(x, y, z)), D = (x, y, z) => DNS.clone().add(V(x, y, z)), S = (x, y, z) => SRV.clone().add(V(x, y, z))
  switch (n) {
    case 'key': { const k = inout(p(s, .7, d)); return [V().lerpVectors(ENTER.clone().add(V(.55, .75, 1.05)), L(2.6, 2.7, 4.6), k), V().lerpVectors(ENTER, L(0, .8, -.5), k)] }
    case 'route': return [V(3.0 - s * .15, 9.5, 13), V(0, 2.3, -1.0)]
    case 'dns': return [D(3.4 - s * .12, 3.8, 10.5), D(-.3, 2.7, 0)]
    case 'tcp': return [V(3.2 - s * .2, 12, 10.5), V(-.4, 2.6, -1.2)]
    case 'tls': { const a = -.45 + s * .16; return [DTOP.clone().add(V(Math.sin(a) * 2.8, .7, Math.cos(a) * 2.8)), DTOP] }
    case 'http': { const k = inout(p(s, .1, 2.0)), k2 = inout(p(s, 1.9, 2.9)); return [V().lerpVectors(D(3.4, 3.4, 7), S(3.6, 4.2, 8.5), k).lerp(V(4.0, 10, 12.5), k2), V().lerpVectors(D(0, 2.8, 0), S(0, 3.2, 0), k).lerp(V(-.6, 2.6, -.6), k2)] }
    case 'render': return [L(1.4 - s * .1, 2.1, 4.6 - s * .2), L(0, 1.0, -.8)]
    default: { const a = .2 + (s + (n === 'cta' ? 2.2 : 0)) * .06; return [V(Math.sin(a) * 12.5, 9.5, Math.cos(a) * 12.5), V(.2, 2.4, -.8)] }
  }
}
function update(t, n, s, d, cam) {
  // Enter key press (frame 0: already halfway down) and the glow under it
  const press = n === 'key' ? (s < .45 ? .55 + .45 * Math.sin(Math.min(1, Math.max(s, 0) / .18) * Math.PI / 2) : 1 - ease(p(s, .45, .7))) : 0
  enterKey.position.y = ENTER_LOCAL.y - press * .03; enterKey.material.emissiveIntensity = press * .9; keyLight.intensity = press * 4
  drawScreen(n === 'key' ? (s < .5 ? 'type' : 'load') : n === 'render' ? 'page' : 'load', n === 'key' ? p(s, .5, d) : n === 'render' ? p(s, 0, d * .9) : 1)
  // server LEDs: random-looking but fixed per frame; a burst while the request arrives
  const burst = n === 'http' && s > 1.6 && s < 2.6
  for (const { led, u, l } of leds) led.visible = hash(u * 3 + l, Math.floor(t * (burst ? 18 : 6))) > (burst ? .25 : .45)
  // hologram + the request parcel
  drawHolo(n === 'dns' ? ease(p(s, .3, .7)) * (1 - p(s, d - .4, d)) : 0, n === 'dns' ? s : 9)
  ring.material.color.setHex(n === 'dns' && s > 2.3 ? GREEN : CYAN)
  let rp = null, rs = 0, rot = n === 'tls' ? 0 : t * .6
  if (n === 'route') { rs = back(p(s, .2, .7)); rp = A.getPoint(.25 * ease(p(s, .2, d))) }
  else if (n === 'dns') { rs = 1; rp = A.getPoint(.25 + .75 * inout(p(s, 0, 1.3))).add(V(0, Math.sin(t * 2) * .04, 0)) }
  else if (n === 'tcp' || n === 'tls') { rs = 1; rp = A.getPoint(1).add(V(0, Math.sin(t * 2) * .04, 0)) }
  else if (n === 'http') { rs = 1 - ease(p(s, 1.55, 1.9)); rp = B.getPoint(inout(p(s, .2, 1.6))) }
  req.visible = rs > .001; if (rp) { req.position.copy(rp); req.scale.setScalar(Math.max(rs, .001)); req.rotation.set(.15, rot, 0) }
  drawTag(req, 'REQUEST · GET /', (n === 'dns' && s > 2.6) || ['tcp', 'tls', 'http'].includes(n) ? '142.250.75.14' : 'TO: ?')
  // TLS: shield flickers on, the lock flies in and its shackle snaps shut
  const tk = n === 'tls' ? 1 : n === 'http' ? 1 : 0, ls = n === 'tls' ? back(p(s, .9, 1.3)) : tk
  lock.visible = tk > 0 && ls > .01; lock.scale.setScalar(Math.max(ls, .01)); lock.position.set(0, .2, req.userData.k / 2 + .1)
  sh.position.y = .14 + (n === 'tls' ? (1 - ease(p(s, 1.4, 1.65))) * .1 : 0)
  shield.material.opacity = n === 'tls' ? .35 * ease(p(s, .3, 1)) * (1 - p(s, 2.6, 3.2)) : 0; shield.rotation.y = t * .5
  // handshake pulses along the direct line (SYN out, SYN-ACK back, ACK out)
  for (const { o, l, i } of pulses) {
    const t0 = .8 + i * .8, k = n === 'tcp' ? inout(p(s, t0, t0 + .75)) : 0, on = n === 'tcp' && s >= t0 && s <= t0 + .95
    o.visible = l.visible = on; if (!on) continue
    const pt = R.getPoint(i === 1 ? k : 1 - k); o.position.copy(pt); l.position.copy(pt).add(V(0, .45, 0))
  }
  // the response parcel rides back on the direct line and drops into the laptop
  const rk = n === 'http' ? inout(p(s, 2.1, 3.4)) : 0
  res.visible = n === 'http' && s > 2.0 && rk < .999; res.position.copy(R.getPoint(rk)); res.scale.setScalar(1.35 * back(p(s, 2.0, 2.3)) * (1 - p(s, 3.3, 3.45)) + .001); res.rotation.set(.1, -t * .7, 0)
  backTube.material.opacity = n === 'tcp' ? .45 * ease(p(s, .3, .8)) : n === 'http' ? .5 * ease(p(s, 1.9, 2.2)) : 0
  holoCard.lookAt(cam.position)
}
laptop.name = 'laptop'; rack.name = 'server'; ped.name = 'DNS stand'; req.name = 'request parcel'; res.name = 'answer parcel'
return { movers: [req, res], solids: [laptop, rack, ped], note: 'FIRST VISIT · VALUES ILLUSTRATIVE', steps: [['DNS', 'dns'], ['TCP', 'tcp'], ['TLS', 'tls'], ['HTTP', 'http'], ['PAINT', 'render']], shot, update }
}
