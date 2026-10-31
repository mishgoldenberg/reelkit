// World for show3d.html ?cfg=tap: "what happens when you tap your card". Payment terminal and card (modelled), the shop's
// processor (server rack), a globe for the card network, the bank (columns + pediment) with three check plates, and the
// scanned parcel carrying the signed payment out and the green "approved" answer back. Stations are stacked in depth so they
// read top-to-bottom in a 9:16 frame.
export default async function ({ THREE, scene, V, clamp, p, ease, inout, back, hash, canvasTex, label, parcel, drawTag, makeRack, RoundedBoxGeometry, CYAN, GREEN }) {
const GOLD = 0xe8c26a
const words = (L, w) => { const x = L.words.find(x => x.w === w); return x ? x.t - L.t0 : 0 }

// ---------- payment terminal (modelled): leaning body, live screen, keypad ----------
const TERM = V(-1.0, 0, 3.6)
const term = new THREE.Group(); term.position.copy(TERM); term.rotation.y = .35; scene.add(term)
const shell = new THREE.MeshStandardMaterial({ color: 0x1b2028, metalness: .55, roughness: .38 })
const stand = new THREE.Mesh(new RoundedBoxGeometry(1.7, .25, 1.5, 4, .08), shell); stand.position.y = .125; stand.castShadow = stand.receiveShadow = true; term.add(stand)
const tilt = new THREE.Group(); tilt.position.set(0, .2, .35); tilt.rotation.x = -1.05; term.add(tilt)       // body leans back
const body = new THREE.Mesh(new RoundedBoxGeometry(1.5, 2.6, .26, 5, .12), shell); body.position.y = 1.3; body.castShadow = true; tilt.add(body)
const ts = canvasTex(600, 520)
const tscreen = new THREE.Mesh(new THREE.PlaneGeometry(1.24, 1.07), new THREE.MeshBasicMaterial({ map: ts.t, toneMapped: false })); tscreen.position.set(0, 1.92, .132); tilt.add(tscreen)
const keyMat = new THREE.MeshStandardMaterial({ color: 0x0e1116, roughness: .5 })
for (let r = 0; r < 4; r++) for (let c = 0; c < 3; c++) {
  const k = new THREE.Mesh(new RoundedBoxGeometry(.32, .18, .06, 2, .03), r === 3 && c === 2 ? new THREE.MeshStandardMaterial({ color: 0x1f7a45, roughness: .5 }) : keyMat)
  k.position.set(-.38 + c * .38, .95 - r * .24, .15); tilt.add(k)
}
const termLabel = label('SHOP TERMINAL', '#e9f1f7', .26); termLabel.position.set(0, 2.6, -.4); term.add(termLabel)
term.updateMatrixWorld(true)
const SCREEN_W = tscreen.localToWorld(V(0, 0, 0)), SCREEN_N = V(0, 0, 1).applyQuaternion(tscreen.getWorldQuaternion(new THREE.Quaternion())).normalize()
function drawTerm(mode, k) {
  const g = ts.g, ok = mode === 'ok'
  g.fillStyle = ok ? '#0f3d24' : '#0c141d'; g.fillRect(0, 0, 600, 520)
  g.textAlign = 'center'; g.textBaseline = 'middle'
  g.font = "700 40px 'JetBrains Mono'"; g.fillStyle = ok ? '#7dffa8' : '#6b7a8a'; g.fillText('TOTAL', 300, 70)
  g.font = "800 120px 'JetBrains Mono'"; g.fillStyle = '#e9f1f7'; g.fillText('42.90', 300, 170)
  if (ok) { g.font = "800 66px 'Inter Tight'"; g.fillStyle = '#7dffa8'; g.fillText('APPROVED ✓', 300, 380) }
  else if (mode === 'wait') { g.font = "700 46px 'JetBrains Mono'"; g.fillStyle = '#3ee6ff'; g.fillText('PROCESSING' + '.'.repeat(1 + Math.floor(k * 6) % 3), 300, 380) }
  else {                                                                                            // contactless waves
    g.strokeStyle = '#3ee6ff'; g.lineWidth = 12; g.lineCap = 'round'
    for (let i = 0; i < 4; i++) { g.globalAlpha = .35 + .65 * ((k * 3 - i * .25) % 1 + 1) % 1; g.beginPath(); g.arc(250, 380, 30 + i * 34, -.7, .7); g.stroke() }
    g.globalAlpha = 1
  }
  ts.t.needsUpdate = true
}

// ---------- the card (modelled): dark gradient, gold chip, contactless mark ----------
const cardTex = (() => {
  const { g, t } = canvasTex(1012, 640)
  const gr = g.createLinearGradient(0, 0, 1012, 640); gr.addColorStop(0, '#0d1b2a'); gr.addColorStop(.6, '#123a52'); gr.addColorStop(1, '#1ea7c4')
  g.fillStyle = gr; g.beginPath(); g.roundRect(0, 0, 1012, 640, 48); g.fill()
  g.fillStyle = '#e8c26a'; g.beginPath(); g.roundRect(110, 210, 150, 115, 18); g.fill()
  g.strokeStyle = '#a8873e'; g.lineWidth = 4; for (const y of [248, 287]) { g.beginPath(); g.moveTo(110, y); g.lineTo(260, y); g.stroke() } g.beginPath(); g.moveTo(185, 210); g.lineTo(185, 325); g.stroke()
  g.strokeStyle = '#e9f1f7'; g.lineWidth = 9; g.lineCap = 'round'; for (let i = 0; i < 4; i++) { g.beginPath(); g.arc(300, 268, 18 + i * 17, -.75, .75); g.stroke() }
  g.fillStyle = '#e9f1f7'; g.font = "600 56px 'JetBrains Mono'"; g.fillText('••••  ••••  ••••  4821', 110, 460)
  g.font = "800 42px 'Inter Tight'"; g.fillText('DEBIT', 110, 560)
  return t
})()
const cardMat = [new THREE.MeshStandardMaterial({ color: 0x0d1b2a, metalness: .6, roughness: .3 })]
const card = new THREE.Group(); scene.add(card)
const slab = new THREE.Mesh(new RoundedBoxGeometry(1.6, 1.01, .03, 3, .012), cardMat[0]); slab.castShadow = true; card.add(slab)
const face = new THREE.Mesh(new THREE.PlaneGeometry(1.58, 1.0), new THREE.MeshStandardMaterial({ map: cardTex, metalness: .15, roughness: .6 })); face.position.z = .016; card.add(face)
const chipGlow = new THREE.PointLight(GOLD, 0, .6, 2); chipGlow.position.set(-.48, .05, .2); card.add(chipGlow)
const ripples = [0, 1, 2].map(() => { const r = new THREE.Mesh(new THREE.TorusGeometry(.5, .012, 8, 64), new THREE.MeshBasicMaterial({ color: CYAN, transparent: true, toneMapped: false, depthWrite: false })); scene.add(r); return r })

// ---------- processor (server rack), network (globe), bank (columns) ----------
const PROC = V(-3.0, 0, -.2)
const { rack, leds } = makeRack(PROC, .5, 'PAYMENT PROCESSOR')
const GLOBE = V(1.7, 2.9, -4.2)
const globe = new THREE.Group(); globe.position.copy(GLOBE); scene.add(globe)
const globeCore = new THREE.Mesh(new THREE.SphereGeometry(1.35, 64, 48), new THREE.MeshStandardMaterial({ color: 0x0b1724, metalness: .3, roughness: .6, emissive: 0x06202c, emissiveIntensity: .6 })); globe.add(globeCore)
globe.add(new THREE.Mesh(new THREE.SphereGeometry(1.37, 24, 16), new THREE.MeshBasicMaterial({ color: CYAN, wireframe: true, transparent: true, opacity: .18, toneMapped: false })))
const cities = []; for (let i = 0; i < 40; i++) {
  const u = hash(i, 1) * Math.PI * 2, v = Math.acos(2 * hash(i, 2) - 1), c = new THREE.Mesh(new THREE.SphereGeometry(.035, 8, 6), new THREE.MeshBasicMaterial({ color: i % 5 ? CYAN : GREEN, toneMapped: false }))
  c.position.setFromSphericalCoords(1.38, v, u); globe.add(c); cities.push(c)
}
const arcs = [[3, 17], [8, 29], [12, 34], [21, 5]].map(([a, b]) => {
  const pa = cities[a].position, pb = cities[b].position, m = pa.clone().add(pb).normalize().multiplyScalar(2.1)
  const tube = new THREE.Mesh(new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(pa, m, pb), 48, .012, 6), new THREE.MeshBasicMaterial({ color: CYAN, transparent: true, opacity: .7, toneMapped: false }))
  globe.add(tube); return tube
})
const orbit = new THREE.Mesh(new THREE.TorusGeometry(1.9, .01, 6, 128), new THREE.MeshBasicMaterial({ color: CYAN, transparent: true, opacity: .4, toneMapped: false })); orbit.rotation.x = 1.25; globe.add(orbit)
const netLabel = label('CARD NETWORK', '#3ee6ff', .28); netLabel.position.set(GLOBE.x, GLOBE.y + 1.95, GLOBE.z); scene.add(netLabel)

const BANK = V(-.6, 0, -8.8)
const bank = new THREE.Group(); bank.position.copy(BANK); bank.rotation.y = .15; scene.add(bank)
const stone = new THREE.MeshStandardMaterial({ color: 0x7d8693, roughness: .7, metalness: .05 })
;[[4.2, .2, 2.8, .1], [3.9, .2, 2.5, .3], [3.6, .2, 2.2, .5]].forEach(([w, h, dd, y]) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, dd), stone); m.position.y = y; m.castShadow = m.receiveShadow = true; bank.add(m) })
for (let i = 0; i < 6; i++) { const c = new THREE.Mesh(new THREE.CylinderGeometry(.16, .18, 2.2, 24), stone); c.position.set(-1.45 + i * .58, 1.7, .75); c.castShadow = true; bank.add(c) }
const wall = new THREE.Mesh(new THREE.BoxGeometry(3.2, 2.2, 1.2), new THREE.MeshStandardMaterial({ color: 0x8f97a3, roughness: .6 })); wall.position.set(0, 1.7, -.2); bank.add(wall)
const beam = new THREE.Mesh(new THREE.BoxGeometry(3.8, .35, 2.3), stone); beam.position.y = 2.97; beam.castShadow = true; bank.add(beam)
const tri = new THREE.Shape(); tri.moveTo(-1.95, 0); tri.lineTo(1.95, 0); tri.lineTo(0, .85); tri.closePath()
const ped = new THREE.Mesh(new THREE.ExtrudeGeometry(tri, { depth: 2.3, bevelEnabled: false }), stone); ped.position.set(0, 3.14, -1.15); ped.castShadow = true; bank.add(ped)
const door = new THREE.Mesh(new THREE.CircleGeometry(.42, 48), new THREE.MeshBasicMaterial({ color: CYAN, toneMapped: false, transparent: true, opacity: .8 })); door.position.set(0, 1.25, .41); bank.add(door)
const bankLabel = label('YOUR BANK', '#e9f1f7', .3); bankLabel.position.set(0, 1.25, 1.6); bank.add(bankLabel)
bank.updateMatrixWorld(true)
const checks = ["IT'S YOUR CARD", 'ENOUGH MONEY', 'NOT FRAUD'].map((txt, i) => {
  const { g, t } = canvasTex(640, 120), m = new THREE.Mesh(new THREE.PlaneGeometry(2.4, .45), new THREE.MeshBasicMaterial({ map: t, transparent: true, toneMapped: false, depthWrite: false }))
  m.position.copy(bank.localToWorld(V(0, 4.45 + (2 - i) * .64, 1.0))); scene.add(m); return { m, g, t, txt }
})
function drawCheck(c, on) {
  const { g, t, txt } = c; g.clearRect(0, 0, 640, 120)
  g.fillStyle = on ? 'rgba(20,70,40,.9)' : 'rgba(10,18,28,.85)'; g.strokeStyle = on ? '#7dffa8' : '#3ee6ff'; g.lineWidth = 5; g.beginPath(); g.roundRect(4, 4, 632, 112, 56); g.fill(); g.stroke()
  g.font = "800 46px 'JetBrains Mono'"; g.fillStyle = on ? '#7dffa8' : '#e9f1f7'; g.textBaseline = 'middle'; g.fillText((on ? '✓ ' : '? ') + txt, 40, 62); t.needsUpdate = true
}

// ---------- routes and the two parcels ----------
rack.updateMatrixWorld(true)
// every stop is in open air: the parcel never touches the card, the rack, the globe or the bank
const START = SCREEN_W.clone().add(SCREEN_N.clone().multiplyScalar(.9)).add(V(0, 1.6, 0)), PFRONT = rack.localToWorld(V(0, 2.4, 1.95))
const G1 = GLOBE.clone().add(V(1.2, -.4, 2.1)), G2 = GLOBE.clone().add(V(2.4, .6, .3)), G3 = GLOBE.clone().add(V(1.4, .9, -1.9)), BIN = bank.localToWorld(V(0, 1.6, 2.7))
const up = (a, b, h, f = .5) => a.clone().lerp(b, f).add(V(0, h, 0))
const A = new THREE.CatmullRomCurve3([START, up(START, PFRONT, 1.2), PFRONT])
const B = new THREE.CatmullRomCurve3([PFRONT, up(PFRONT, G1, 1.4), G1])
const C = new THREE.CatmullRomCurve3([G1, G2, G3, up(G3, BIN, .8), BIN])
const R = new THREE.CatmullRomCurve3([BIN, up(BIN, START, 3.6, .3).add(V(-1.8, 0, 0)), up(BIN, START, 3.2, .7).add(V(1.4, 0, 0)), START])   // high arc that clears the globe
const tube = (cv, c, o) => { const m = new THREE.Mesh(new THREE.TubeGeometry(cv, 240, .018, 8), new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: o, toneMapped: false, depthWrite: false })); scene.add(m); return m }
tube(A, CYAN, .35); tube(B, CYAN, .35); tube(C, CYAN, .35); const backTube = tube(R, GREEN, 0)
const pay = parcel('#3ee6ff'), ans = parcel('#7dffa8')
drawTag(pay, 'PAYMENT · SIGNED', '42.90'); drawTag(ans, 'ANSWER', 'APPROVED')
const ansGlow = new THREE.PointLight(GREEN, 6, 3, 2); ans.add(ansGlow)
const seal = new THREE.Mesh(new THREE.CylinderGeometry(.13, .13, .04, 32), new THREE.MeshStandardMaterial({ color: GOLD, metalness: 1, roughness: .25, emissive: GOLD, emissiveIntensity: .35 }))
seal.rotation.x = Math.PI / 2; pay.add(seal)
// light beam from the chip up to where the signed payment appears
const chipBeam = new THREE.Mesh(new THREE.CylinderGeometry(.02, .02, 1, 8), new THREE.MeshBasicMaterial({ color: GOLD, transparent: true, toneMapped: false, depthWrite: false })); scene.add(chipBeam)

// ---------- camera ----------
const Tm = (x, y, z) => TERM.clone().add(V(x, y, z)), Pr = (x, y, z) => PROC.clone().add(V(x, y, z)), Bk = (x, y, z) => BANK.clone().add(V(x, y, z))
const CARD_TAP = SCREEN_W.clone().add(SCREEN_N.clone().multiplyScalar(.12)), CARD_OUT = SCREEN_W.clone().add(SCREEN_N.clone().multiplyScalar(.9))
const CARD_Q = tscreen.getWorldQuaternion(new THREE.Quaternion()).multiply(new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), .25))
const CHIP_W = V(-.48, .05, 0).applyQuaternion(CARD_Q).add(CARD_OUT)   // fixed, so the camera never depends on last frame's state
function shot(n, s, d) {
  switch (n) {
    case 'tap': { const k = inout(p(s, .9, d)); return [V().lerpVectors(CARD_TAP.clone().add(V(1.5, 1.4, 3.0)), Tm(2.6, 3.4, 5.6), k), V().lerpVectors(CARD_TAP, Tm(0, 1.1, -.2), k)] }
    case 'chip': { const k = inout(p(s, 1.3, 2.6)); return [V().lerpVectors(CHIP_W.clone().add(V(.9, .8, 1.9)), START.clone().add(V(2.2, .2, 6.8)), k), V().lerpVectors(CHIP_W.clone().add(V(.25, 0, 0)), START.clone().lerp(CHIP_W, .62), k)] }
    case 'shop': return [V(2.6 - s * .2, 6.5, 10.5), V(-2.0, 2.0, 1.2)]
    case 'network': return [GLOBE.clone().add(V(3.2 - s * .25, 2.4, 10.5)), GLOBE.clone().add(V(-.6, .9, 0))]
    case 'bank': return [Bk(-.4 + s * .06, 6.2, 13.5), Bk(-.2, 4.1, 0)]
    case 'back': { const k = inout(p(s, 0, d)); return [V().lerpVectors(Bk(-3.5, 9, 12), V(-2.5, 11, 13.5), k), V().lerpVectors(Bk(0, 2.6, 0), V(-.3, 2.2, -1.6), k)] }
    case 'approved': return [Tm(1.2, 3.0 - s * .1, 3.9 - s * .15), Tm(0, 1.3, -.4)]
    default: { const a = .3 + s * .06; return [V(Math.sin(a) * 14, 10.5, Math.cos(a) * 14 - 1.5), V(.2, 2.6, -2.2)] }
  }
}

// ---------- per frame ----------
function update(t, n, s, d, cam, L) {
  // the card: frame 0 it is already touching the screen; it lifts off, then sits by the terminal
  let tap = n === 'tap' ? (s < .5 ? 1 : 1 - ease(p(s, .5, 1.1))) : 0
  card.position.copy(CARD_OUT).lerp(CARD_TAP, tap); card.quaternion.copy(CARD_Q)
  if (n !== 'tap' && n !== 'chip' && n !== 'approved') card.position.add(V(0, Math.sin(t * 1.6) * .03, 0))
  ripples.forEach((r, i) => { const k = ((Math.max(s, 0) + i * .33) % 1); const on = n === 'tap' && s < 1.6
    r.visible = on; r.position.copy(CARD_TAP); r.quaternion.copy(card.quaternion); r.scale.setScalar(.4 + k * 1.6); r.material.opacity = (1 - k) * .8 })
  chipGlow.intensity = n === 'chip' ? .35 * ease(p(s, .3, .8)) : 0
  drawTerm(n === 'approved' || n === 'cta' ? 'ok' : n === 'tap' && s < 1.2 ? 'tap' : n === 'tap' ? 'wait' : 'wait', t)
  // server LEDs, burst while the payment passes through
  const burst = n === 'shop' && s > 1.2
  for (const { led, u, l } of leds) led.visible = hash(u * 3 + l, Math.floor(t * (burst ? 18 : 6))) > (burst ? .25 : .45)
  globe.rotation.y = t * .25; arcs.forEach((a, i) => a.material.opacity = n === 'network' ? .4 + .6 * Math.abs(Math.sin(t * 3 + i)) : .35)
  // the signed payment: born at the chip, rides A -> B -> C into the bank
  let pp = null, ps = 0
  if (n === 'chip') { ps = back(p(s, 1.9, 2.4)); pp = START.clone() }
  else if (n === 'shop') { ps = 1; pp = A.getPoint(inout(p(s, 0, 1.4))) }
  else if (n === 'network') { ps = 1; const k = inout(p(s, 0, d - .2)); pp = k < .35 ? B.getPoint(k / .35) : C.getPoint(((k - .35) / .65) * .62) }
  else if (n === 'bank') { ps = 1 - ease(p(s, d - .6, d - .2)); pp = C.getPoint(.62 + .38 * inout(p(s, 0, 1.2))) }
  pay.visible = ps > .001; if (pp) { pay.position.copy(pp); pay.scale.setScalar(Math.max(ps, .001)); pay.rotation.set(.12, t * .6, 0) }
  seal.position.set(.22, -.12, pay.userData.k / 2 + .03)
  const bk = n === 'chip' ? ease(p(s, 1.2, 1.9)) * (1 - p(s, 2.4, 2.9)) : 0; chipBeam.visible = bk > .01
  if (bk > .01) { const a = CHIP_W, b = a.clone().lerp(START, ease(p(s, 1.2, 1.9))); chipBeam.position.copy(a).lerp(b, .5); chipBeam.scale.set(1, a.distanceTo(b), 1); chipBeam.quaternion.setFromUnitVectors(V(0, 1, 0), b.clone().sub(a).normalize()); chipBeam.material.opacity = bk }
  // the bank's three checks light up on the words "card?", "money?", "fraud?"
  checks.forEach((c, i) => {
    const at = n === 'bank' ? words(L, ['card?', 'money?', 'fraud?'][i]) : 0, vis = n === 'bank' ? back(p(s, .9 + i * .2, 1.2 + i * .2)) : n === 'back' ? 1 - p(s, 0, .4) : 0
    c.m.visible = vis > .01; c.m.scale.setScalar(Math.max(vis, .01)); c.m.lookAt(cam.position); drawCheck(c, n === 'back' || (n === 'bank' && s >= at + .1))
  })
  door.material.color.setHex(n === 'bank' && s > words(L, 'fraud?') + .2 || n === 'back' ? GREEN : CYAN)
  // the answer flies all the way back to the terminal
  const ak = n === 'back' ? inout(p(s, .15, d - .1)) : 0
  ans.visible = n === 'back' && ak < .999; ans.position.copy(R.getPoint(ak)); ans.scale.setScalar(1.35 * back(p(s, 0, .3)) * (1 - p(ak, .85, .99)) + .001); ans.rotation.set(.1, -t * .7, 0)
  backTube.material.opacity = n === 'back' ? .55 * ease(p(s, 0, .4)) : 0
  netLabel.visible = true; termLabel.visible = n !== 'chip'
}
term.name = 'terminal'; card.name = 'card'; rack.name = 'processor'; bank.name = 'bank'; globeCore.name = 'globe'; pay.name = 'payment parcel'; ans.name = 'answer parcel'
return { movers: [pay, ans], solids: [term, card, rack, bank, globeCore], note: 'VALUES ILLUSTRATIVE', steps: [['CHIP', 'chip'], ['SHOP', 'shop'], ['NETWORK', 'network'], ['BANK', 'bank'], ['BACK', 'back']], shot, update }
}
