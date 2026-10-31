// World for show3d.html ?cfg=cloud: "what happens in cloud gaming" (generic, no service named). Gamepad and TV (modelled),
// a data center (three racks) with a graphics card in front, the input packet flying out, the rendered frame squeezed into
// video and streamed back to the TV, where the game character finally jumps. Stations stacked in depth for 9:16.
export default async function ({ THREE, scene, V, clamp, p, ease, inout, back, hash, canvasTex, label, makeRack, RoundedBoxGeometry, CYAN, GREEN }) {
const MAG = 0xff5ad1

// ---------- TV with the game on it ----------
const TVP = V(-.9, 0, 2.9)
const tv = new THREE.Group(); tv.position.copy(TVP); tv.rotation.y = .32; scene.add(tv)
const black = new THREE.MeshStandardMaterial({ color: 0x0d1015, metalness: .6, roughness: .35 })
const foot = new THREE.Mesh(new RoundedBoxGeometry(1.4, .08, .7, 3, .03), black); foot.position.y = .04; tv.add(foot)
const neck = new THREE.Mesh(new THREE.BoxGeometry(.14, 1.0, .1), black); neck.position.set(0, .55, -.1); tv.add(neck)
const bezel = new THREE.Mesh(new RoundedBoxGeometry(3.3, 1.95, .12, 4, .04), black); bezel.position.set(0, 2.0, 0); bezel.castShadow = true; tv.add(bezel)
const gs = canvasTex(960, 540)
const screen = new THREE.Mesh(new THREE.PlaneGeometry(3.12, 1.76), new THREE.MeshBasicMaterial({ map: gs.t, toneMapped: false })); screen.position.set(0, 2.0, .062); tv.add(screen)
const tvLabel = label('YOUR SCREEN', '#e9f1f7', .26); tvLabel.position.set(0, 3.3, 0); tv.add(tvLabel)
function drawGame(g, jump, frameNo) {                                                             // a tiny platformer
  const sky = g.createLinearGradient(0, 0, 0, 540); sky.addColorStop(0, '#1d2b6b'); sky.addColorStop(1, '#5a3a8c'); g.fillStyle = sky; g.fillRect(0, 0, 960, 540)
  g.fillStyle = 'rgba(255,255,255,.7)'; for (let i = 0; i < 30; i++) g.fillRect((hash(i, 3) * 960 - frameNo * 2) % 960 + (hash(i, 3) * 960 - frameNo * 2 < 0 ? 960 : 0), hash(i, 4) * 300, 3, 3)
  g.fillStyle = '#2a1846'; for (let i = 0; i < 6; i++) { const x = ((i * 220 - frameNo * 4) % 1320 + 1320) % 1320 - 180; g.beginPath(); g.moveTo(x, 420); g.lineTo(x + 110, 250); g.lineTo(x + 220, 420); g.fill() }
  g.fillStyle = '#7dffa8'; g.fillRect(0, 420, 960, 14); g.fillStyle = '#1b6b4a'; g.fillRect(0, 434, 960, 106)
  for (let i = 0; i < 12; i++) { const x = ((i * 90 - frameNo * 4) % 1080 + 1080) % 1080 - 60; g.fillStyle = '#145238'; g.fillRect(x, 450, 40, 18) }
  const y = 420 - 70 - jump * 150                                                                      // the hero
  g.fillStyle = '#3ee6ff'; g.beginPath(); g.roundRect(300, y, 60, 70, 12); g.fill()
  g.fillStyle = '#05070b'; g.fillRect(338, y + 18, 10, 12)
  g.fillStyle = '#ffcf5a'; g.beginPath(); g.arc(620, 300 - Math.sin(frameNo / 6) * 10, 18, 0, 7); g.fill()
}

// ---------- gamepad (modelled) ----------
const PADP = V(1.7, 1.25, 5.0)
const pad = new THREE.Group(); pad.position.copy(PADP); pad.rotation.set(-.95, -.35, 0); scene.add(pad)
const padMat = new THREE.MeshStandardMaterial({ color: 0x20252e, metalness: .3, roughness: .45 })
const pbody = new THREE.Mesh(new RoundedBoxGeometry(1.5, .32, .8, 5, .14), padMat); pbody.castShadow = true; pad.add(pbody)
for (const sx of [-1, 1]) { const grip = new THREE.Mesh(new RoundedBoxGeometry(.48, .3, .78, 5, .14), padMat); grip.position.set(sx * .62, -.03, .32); grip.rotation.y = sx * .35; pad.add(grip) }
const stickMat = new THREE.MeshStandardMaterial({ color: 0x0c0e12, roughness: .7 })
for (const [x, z] of [[.38, -.08], [-.2, .17]]) { const st = new THREE.Mesh(new THREE.CylinderGeometry(.1, .1, .1, 24), stickMat); st.position.set(x, .2, z); pad.add(st) }
const btnCols = [[GREEN, -.48, .1], [0xff6159, -.6, -.02], [CYAN, -.36, -.02], [0xffcf5a, -.48, -.14]]   // x mirrored: this pad is seen from its far side, so buttons read on the right
const buttons = btnCols.map(([c, x, z]) => { const b = new THREE.Mesh(new THREE.CylinderGeometry(.065, .065, .06, 24), new THREE.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: .25, roughness: .3 })); b.position.set(x, .18, z); pad.add(b); return b })
const A = buttons[0]
for (const [w, d] of [[.26, .08], [.08, .26]]) { const dp = new THREE.Mesh(new THREE.BoxGeometry(w, .05, d), stickMat); dp.position.set(.45, .17, -.14); pad.add(dp) }
const aLight = new THREE.PointLight(GREEN, 0, 1.5, 2); A.add(aLight); aLight.position.y = .2
pad.updateMatrixWorld(true)
const AW = A.getWorldPosition(V(0, 0, 0)), PAD_N = V(0, 1, 0).applyQuaternion(pad.quaternion).normalize()   // the way the buttons face

// ---------- data center: three racks and the graphics card ----------
const racks = [-2.7, 0, 2.7].map((x, i) => makeRack(V(x, 0, -6.4), 0, i === 1 ? 'DATA CENTER' : 'RACK'))
racks.forEach((r, i) => { if (i !== 1) r.rack.children[r.rack.children.length - 1].visible = false })
const GPUP = V(0, 2.5, -3.8)
const gpu = new THREE.Group(); gpu.position.copy(GPUP); scene.add(gpu)
const shroud = new THREE.Mesh(new RoundedBoxGeometry(2.7, 1.15, .32, 4, .06), new THREE.MeshStandardMaterial({ color: 0x1a1f27, metalness: .8, roughness: .3 })); shroud.castShadow = true; gpu.add(shroud)
const pcb = new THREE.Mesh(new THREE.BoxGeometry(2.6, 1.05, .05), new THREE.MeshStandardMaterial({ color: 0x0f2a1d, roughness: .6 })); pcb.position.z = -.19; gpu.add(pcb)
const stripe = new THREE.Mesh(new THREE.BoxGeometry(2.5, .04, .02), new THREE.MeshBasicMaterial({ color: CYAN, toneMapped: false })); stripe.position.set(0, -.5, .17); gpu.add(stripe)
const fans = [-.68, .68].map(x => {
  const f = new THREE.Group(); f.position.set(x, 0, .17); gpu.add(f)
  const ring = new THREE.Mesh(new THREE.TorusGeometry(.44, .03, 8, 48), new THREE.MeshStandardMaterial({ color: 0x2b3340, metalness: .8, roughness: .3 })); f.add(ring)
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(.12, .12, .05, 24), new THREE.MeshStandardMaterial({ color: 0x0c0e12 })); hub.rotation.x = Math.PI / 2; f.add(hub)
  const blades = new THREE.Group(); f.add(blades)
  for (let i = 0; i < 9; i++) { const b = new THREE.Mesh(new THREE.BoxGeometry(.34, .1, .015), new THREE.MeshStandardMaterial({ color: 0x14181e, roughness: .5 })); b.position.set(Math.cos(i / 9 * 6.283) * .26, Math.sin(i / 9 * 6.283) * .26, 0); b.rotation.set(.35, 0, i / 9 * 6.283); blades.add(b) }
  return blades
})
const gpuLabel = label('GRAPHICS CARD', '#3ee6ff', .26); gpuLabel.position.set(0, 1.0, 0); gpu.add(gpuLabel)
const gpuGlow = new THREE.PointLight(CYAN, 0, 4, 2); gpuGlow.position.set(0, 0, 1.0); gpu.add(gpuGlow)

// ---------- moving things: input packet, the frame, the stream ----------
tv.updateMatrixWorld(true)
const SCREEN_W = screen.getWorldPosition(V(0, 0, 0)), TV_N = V(0, 0, 1).applyQuaternion(screen.getWorldQuaternion(new THREE.Quaternion()))
const PAD_UP = AW.clone().add(V(0, .9, 0)), FRAME0 = V(0, 2.5, -2.3), TV_IN = SCREEN_W.clone().add(TV_N.clone().multiplyScalar(1.3))
const IN_END = V(.0, 3.5, -2.9)
const PathA = new THREE.CatmullRomCurve3([PAD_UP, V(1.6, 3.6, 2.4), V(.8, 4.0, -.6), IN_END])
const PathR = new THREE.CatmullRomCurve3([FRAME0, V(.5, 4.3, -.3), TV_IN.clone().add(V(.7, 1.9, .5)), TV_IN])   // over the TV and down to the front of the screen
const tubeM = (c, o) => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: o, toneMapped: false, depthWrite: false })
scene.add(new THREE.Mesh(new THREE.TubeGeometry(PathA, 200, .016, 8), tubeM(CYAN, .3)))
const backTube = new THREE.Mesh(new THREE.TubeGeometry(PathR, 200, .016, 8), tubeM(MAG, 0)); scene.add(backTube)
const pkt = new THREE.Mesh(new THREE.CapsuleGeometry(.11, .3, 8, 16), new THREE.MeshBasicMaterial({ color: CYAN, toneMapped: false })); scene.add(pkt)
const pktLabel = label('JUMP', '#3ee6ff', .24); scene.add(pktLabel)
const fs = canvasTex(480, 270)
const frame = new THREE.Mesh(new RoundedBoxGeometry(1.6, .9, .03, 2, .012), [0, 1, 2, 3, 4, 5].map(i => i === 4 ? new THREE.MeshBasicMaterial({ map: fs.t, toneMapped: false }) : new THREE.MeshStandardMaterial({ color: 0x0d1015 })))
scene.add(frame)
const vid = new THREE.Mesh(new RoundedBoxGeometry(.42, .42, .42, 3, .06), new THREE.MeshStandardMaterial({ color: 0x2a0f2a, emissive: MAG, emissiveIntensity: .9, metalness: .3, roughness: .3 })); scene.add(vid)
const vidLabel = label('VIDEO', '#ff5ad1', .22); scene.add(vidLabel)
const stream = Array.from({ length: 8 }, () => { const m = new THREE.Mesh(new RoundedBoxGeometry(.3, .3, .3, 2, .05), new THREE.MeshStandardMaterial({ color: 0x2a0f2a, emissive: MAG, emissiveIntensity: .9 })); scene.add(m); return m })
const rate = label('60 FRAMES / SECOND', '#ff5ad1', .3); rate.position.set(-.4, 4.6, .6); scene.add(rate)

// ---------- camera ----------
const shotOf = (pos, tgt) => [pos, tgt]
function shot(n, s, d) {
  switch (n) {
    case 'press': { const k = inout(p(s, .9, d)); return [V().lerpVectors(PADP.clone().add(PAD_N.clone().multiplyScalar(4.6)).add(V(.9, .3, 0)), V(2.6, 4.6, 10.5), k), V().lerpVectors(PADP.clone().add(V(.75, 0, 0)), V(.2, 1.9, 2.4), k)] }
    case 'input': return [V(4.0 - s * .3, 7.5, 12.5), V(.3, 2.6, -1.4)]
    case 'gpu': return [GPUP.clone().add(V(1.6 - s * .12, .7, 4.6)), GPUP.clone().add(V(0, -.1, 1.0))]
    case 'encode': return [FRAME0.clone().add(V(1.3, .7, 4.4 - s * .1)), FRAME0.clone().add(V(0, .3, 0))]
    case 'stream': { const k = inout(p(s, 0, d)); return [V().lerpVectors(V(2.6, 5.5, 7.5), TVP.clone().add(V(1.6, 2.6, 6.2)), k), V().lerpVectors(V(-.3, 2.8, -.5), TVP.clone().add(V(0, 2.0, 0)), k)] }
    case 'repeat': return [V(3.4 - s * .2, 7.5, 13), V(-.2, 2.8, -1.6)]
    default: { const a = .25 + s * .07; return [V(Math.sin(a) * 13.5, 9.5, Math.cos(a) * 13.5 - 1.2), V(0, 2.6, -1.4)] }
  }
}

// ---------- per frame ----------
const hidden = o => { o.visible = false }
function update(t, n, s, d, cam, L) {
  // A button: frame 0 it is already going down
  const press = n === 'press' ? (s < .45 ? .55 + .45 * Math.sin(Math.min(1, Math.max(s, 0) / .18) * Math.PI / 2) : 1 - ease(p(s, .45, .7))) : 0
  A.position.y = .18 - press * .035; A.material.emissiveIntensity = .25 + press * .45; aLight.intensity = press * .6
  // the game: the hero only jumps once the streamed frame arrives (that is the latency you feel)
  const jump = n === 'stream' ? Math.sin(Math.PI * p(s, 1.3, 2.3)) : n === 'repeat' ? Math.max(0, Math.sin(t * 5)) * .6 : 0
  drawGame(gs.g, jump, Math.floor(t * 30)); gs.t.needsUpdate = true
  // fans spin, faster while rendering
  const busy = ['gpu', 'encode', 'repeat'].includes(n); fans.forEach((b, i) => { b.rotation.z = t * (busy ? 22 : 6) * (i ? -1 : 1) })
  gpuGlow.intensity = n === 'gpu' ? 8 * ease(p(s, .3, .9)) : busy ? 4 : 0
  // input packet: pad -> data center
  const pk = n === 'input' ? inout(p(s, .2, d - .2)) : 0, pkOn = n === 'input' && s > .15 && pk < .98
  pkt.visible = pktLabel.visible = pkOn
  if (pkOn) { const q = PathA.getPoint(pk), tg = PathA.getTangent(pk); pkt.position.copy(q); pkt.quaternion.setFromUnitVectors(V(0, 1, 0), tg); pktLabel.position.copy(q).add(V(0, .4, 0)); pkt.scale.setScalar(back(p(s, .15, .4)) * (1 - p(pk, .9, .98)) + .001) }
  // the frame appears in front of the card (gpu), then squeezes into a video block (encode)
  const fOn = n === 'gpu' && s > .9 || n === 'encode'
  frame.visible = fOn && !(n === 'encode' && s > 1.45)   // the block takes its place, never both at once
  if (fOn) {
    const sq = n === 'encode' ? ease(p(s, .5, 1.5)) : 0
    frame.position.copy(FRAME0); frame.rotation.set(0, n === 'gpu' ? -.25 + p(s, .9, d) * .25 : 0, 0)
    frame.scale.set((n === 'gpu' ? back(p(s, .9, 1.4)) : 1) * (1 - sq * .74), (n === 'gpu' ? back(p(s, .9, 1.4)) : 1) * (1 - sq * .53), 1 + sq * 12)
    fs.g.drawImage(gs.c, 0, 0, 480, 270); fs.t.needsUpdate = true
  }
  // the video block: born where the frame was squeezed, rides back to the TV
  const vk = n === 'stream' ? inout(p(s, 0, 1.25)) : 0
  const vOn = n === 'encode' && s > 1.45 || n === 'stream' && vk < .98
  vid.visible = vidLabel.visible = vOn
  if (vOn) { const q = n === 'encode' ? FRAME0 : PathR.getPoint(vk); vid.position.copy(q); vid.rotation.set(t * .8, t * 1.1, 0); vid.scale.setScalar((n === 'encode' ? back(p(s, 1.45, 1.75)) : 1) * (1 - p(vk, .88, .98)) + .001); vidLabel.position.copy(q).add(V(0, .48, 0)) }
  backTube.material.opacity = n === 'stream' || n === 'repeat' ? .4 : 0
  // repeat: a steady stream of frames
  stream.forEach((m, i) => { const k = ((t * .9 + i / stream.length) % 1); const on = n === 'repeat' && s > .2 && k < .95
    m.visible = on; if (on) { m.position.copy(PathR.getPoint(k)); m.rotation.set(t + i, t * 1.3 + i, 0); m.scale.setScalar(1 - p(k, .85, .95) + .001) } })
  rate.visible = n === 'repeat'; rate.scale.set(1.2 * back(p(s, .1, .4)) + .001, .3 * back(p(s, .1, .4)) + .001, 1)
}
tv.name = 'TV'; pad.name = 'gamepad'; gpu.name = 'graphics card'; racks.forEach((r, i) => r.rack.name = 'rack ' + (i + 1))
pkt.name = 'input packet'; frame.name = 'frame'; vid.name = 'video block'; stream.forEach((m, i) => m.name = 'stream frame ' + i)
return { movers: [pkt, frame, vid, ...stream], solids: [tv, pad, gpu, ...racks.map(r => r.rack)], note: 'VALUES ILLUSTRATIVE',
  steps: [['INPUT', 'input'], ['RENDER', 'gpu'], ['ENCODE', 'encode'], ['STREAM', 'stream'], ['×60', 'repeat']], shot, update }
}
