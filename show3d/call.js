// World for show3d.html ?cfg=call: "what happens in a video call" (generic, no app named). Faceless mannequins at desks
// (you in front, three friends at the back), real laptops with a camera dot, a call server (rack) in the middle that copies
// your stream to everyone. Pictures fly out of the camera, get squeezed to "what changed", your echo is cancelled, the
// packets fan out and the friends' screens light up. Over-the-shoulder framing so your laptop screen (the call grid) shows.
export default async function ({ THREE, scene, V, clamp, p, ease, inout, back, hash, canvasTex, label, makeRack, RoundedBoxGeometry, CYAN, GREEN }) {
const AMBER = 0xffcf5a, RED = 0xff6159
const skin = new THREE.MeshStandardMaterial({ color: 0xb7c0ca, roughness: .55, metalness: .05 })
const wood = new THREE.MeshStandardMaterial({ color: 0x2a2f38, roughness: .6, metalness: .2 })
const alu = new THREE.MeshStandardMaterial({ color: 0x3b4048, metalness: .9, roughness: .32 })

// a faceless mannequin at a desk with a laptop; the group faces -z (the laptop is in front of the person at local -z)
function person(pos, rotY, shirt, name) {
  const g = new THREE.Group(); g.position.copy(pos); g.rotation.y = rotY; scene.add(g)
  const top = new THREE.Mesh(new RoundedBoxGeometry(1.9, .07, 1.0, 3, .03), wood); top.position.set(0, .95, -.7); top.castShadow = top.receiveShadow = true; g.add(top)
  for (const [x, z] of [[-.85, -.3], [.85, -.3], [-.85, -1.1], [.85, -1.1]]) { const l = new THREE.Mesh(new THREE.BoxGeometry(.06, .92, .06), wood); l.position.set(x, .46, z); g.add(l) }
  const seat = new THREE.Mesh(new RoundedBoxGeometry(.7, .1, .6, 3, .04), wood); seat.position.set(0, .55, .45); g.add(seat)
  const backr = new THREE.Mesh(new RoundedBoxGeometry(.7, .8, .08, 3, .04), wood); backr.position.set(0, 1.0, .78); g.add(backr)
  const leg = new THREE.Mesh(new THREE.CylinderGeometry(.05, .05, .5, 12), wood); leg.position.set(0, .28, .45); g.add(leg)
  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(.27, .5, 8, 16), new THREE.MeshStandardMaterial({ color: shirt, roughness: .7 })); torso.position.set(0, 1.12, .42); torso.castShadow = true; g.add(torso)
  const headG = new THREE.Group(); headG.position.set(0, 1.72, .38); g.add(headG)
  const head = new THREE.Mesh(new THREE.SphereGeometry(.24, 32, 24), skin); head.scale.set(.9, 1.08, .95); head.castShadow = true; headG.add(head)
  const neck = new THREE.Mesh(new THREE.CylinderGeometry(.08, .09, .16, 12), skin); neck.position.set(0, 1.55, .42); g.add(neck)
  for (const sx of [-1, 1]) {                                                                        // arms resting on the desk
    const up = new THREE.Mesh(new THREE.CapsuleGeometry(.08, .32, 6, 12), new THREE.MeshStandardMaterial({ color: shirt, roughness: .7 }))
    up.position.set(sx * .33, 1.12, .25); up.rotation.x = .9; g.add(up)
    const fore = new THREE.Mesh(new THREE.CapsuleGeometry(.07, .3, 6, 12), skin); fore.position.set(sx * .3, 1.04, -.1); fore.rotation.x = 1.45; g.add(fore)
  }
  // laptop on the desk, screen facing the person (+z)
  const lap = new THREE.Group(); lap.position.set(0, .99, -.75); g.add(lap)
  const base = new THREE.Mesh(new RoundedBoxGeometry(1.1, .05, .75, 3, .02), alu); lap.add(base)
  const hinge = new THREE.Group(); hinge.position.set(0, .025, -.37); hinge.rotation.x = .22; lap.add(hinge)
  const lid = new THREE.Mesh(new RoundedBoxGeometry(1.1, .72, .03, 3, .012), alu); lid.position.set(0, .36, 0); hinge.add(lid)
  const sc = canvasTex(640, 400)
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(1.02, .64), new THREE.MeshBasicMaterial({ map: sc.t, toneMapped: false })); screen.position.set(0, .36, .017); hinge.add(screen)
  const lens = new THREE.Mesh(new THREE.CircleGeometry(.018, 16), new THREE.MeshBasicMaterial({ color: GREEN, toneMapped: false })); lens.position.set(0, .7, .017); hinge.add(lens)
  g.name = name; g.updateMatrixWorld(true)
  return { g, headG, sc, lens, screen, lap }
}
const YOU = person(V(-1.0, 0, 3.6), .25, 0x2b6cff, 'you')
const friends = [[-2.9, -5.6, .15, 0xff6159], [0, -6.2, 0, 0x7dffa8], [2.9, -5.6, -.15, 0xffcf5a]].map(([x, z, r, c], i) => person(V(x, 0, z), Math.PI + r, c, 'friend ' + (i + 1)))
const youLabel = label('YOU', '#e9f1f7', .26); youLabel.position.set(0, 2.35, .4); YOU.g.add(youLabel)
const { rack, leds } = makeRack(V(2.3, 0, -1.4), -.5, 'CALL SERVER'); rack.name = 'call server'

// screens: your laptop shows the call grid; friends' laptops show you
function silhouette(g, x, y, w, h, bg, shirt, talk) {
  g.fillStyle = bg; g.beginPath(); g.roundRect(x, y, w, h, 14); g.fill()
  g.fillStyle = shirt; g.beginPath(); g.ellipse(x + w / 2, y + h * .98, w * .3, h * .3, 0, Math.PI, 0); g.fill()
  g.fillStyle = '#b7c0ca'; g.beginPath(); g.ellipse(x + w / 2, y + h * .45, w * .12, h * .18, 0, 0, 7); g.fill()
  if (talk) { g.strokeStyle = '#7dffa8'; g.lineWidth = 6; g.beginPath(); g.roundRect(x + 3, y + 3, w - 6, h - 6, 12); g.stroke() }
}
function drawYouScreen(talker) {
  const g = YOU.sc.g; g.fillStyle = '#0b1118'; g.fillRect(0, 0, 640, 400)
  const cols = ['#ff6159', '#7dffa8', '#ffcf5a']
  cols.forEach((c, i) => silhouette(g, 14 + i * 208, 40, 196, 250, '#16202c', c, talker === i))
  silhouette(g, 470, 300, 150, 90, '#1d2a3a', '#2b6cff', talker === -1)
  g.fillStyle = RED_S; g.beginPath(); g.arc(320, 345, 22, 0, 7); g.fill()
  YOU.sc.t.needsUpdate = true
}
const RED_S = '#ff6159'
function drawFriendScreen(f, on) { const g = f.sc.g; g.fillStyle = '#0b1118'; g.fillRect(0, 0, 640, 400); if (on) silhouette(g, 120, 20, 400, 360, '#16202c', '#2b6cff', true); f.sc.t.needsUpdate = true }

// ---------- moving things ----------
const LENS = YOU.lens.getWorldPosition(V(0, 0, 0))
const YOU_HEAD = YOU.headG.getWorldPosition(V(0, 0, 0))
rack.updateMatrixWorld(true)
const SRV = rack.localToWorld(V(0, 2.5, 1.9)), OUT = LENS.clone().add(V(.6, 1.3, -.6))
const toServer = new THREE.CatmullRomCurve3([OUT, OUT.clone().lerp(SRV, .5).add(V(0, 1.4, 0)), SRV])
const fanout = friends.map(f => { const fh = f.headG.getWorldPosition(V(0, 0, 0)).add(V(0, 1.2, .4)); const fi = friends.indexOf(f), s0 = SRV.clone().add(V((fi - 1) * .6, (1 - Math.abs(fi - 1)) * .5, 0))   // each copy leaves from its own spot
  return new THREE.CatmullRomCurve3([s0, s0.clone().add(V((fi - 1) * .5, 2.4, .6)), SRV.clone().lerp(fh, .55).add(V(0, 3.2, 0)), fh]) })   // up and over the rack
const tubeM = (c, o) => new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: o, toneMapped: false, depthWrite: false })
const tubes = [toServer, ...fanout].map((cv, i) => { const m = new THREE.Mesh(new THREE.TubeGeometry(cv, 160, .015, 8), tubeM(i ? GREEN : CYAN, 0)); scene.add(m); return m })
// photos out of the camera (30 a second): thin cards with your silhouette
const pc = canvasTex(320, 200); silhouette(pc.g, 0, 0, 320, 200, '#1d2a3a', '#2b6cff', false); pc.t.needsUpdate = true
const diff = canvasTex(320, 200); { const g = diff.g; g.fillStyle = 'rgba(29,42,58,.25)'; g.fillRect(0, 0, 320, 200); g.fillStyle = '#3ee6ff'; g.beginPath(); g.roundRect(118, 40, 84, 100, 14); g.fill(); g.fillStyle = '#05070b'; g.font = "800 22px 'JetBrains Mono'"; g.textAlign = 'center'; g.fillText('CHANGED', 160, 96); diff.t.needsUpdate = true }
const cardMat = new THREE.MeshBasicMaterial({ map: pc.t, toneMapped: false }), diffMat = new THREE.MeshBasicMaterial({ map: diff.t, toneMapped: false, transparent: true })
const cards = Array.from({ length: 6 }, (_, i) => { const m = new THREE.Mesh(new RoundedBoxGeometry(.64, .4, .02, 2, .01), [0, 1, 2, 3, 4, 5].map(j => j === 4 ? cardMat : new THREE.MeshStandardMaterial({ color: 0x0d1015 }))); scene.add(m); m.name = 'photo ' + i; return m })
const slim = new THREE.Mesh(new RoundedBoxGeometry(.64, .4, .02, 2, .01), [0, 1, 2, 3, 4, 5].map(j => j === 4 ? diffMat : new THREE.MeshStandardMaterial({ color: 0x0d1015, transparent: true, opacity: .3 }))); scene.add(slim); slim.name = 'squeezed photo'
const rateL = label('30 / SECOND', '#3ee6ff', .26); scene.add(rateL)
const diffL = label('ONLY WHAT CHANGED', '#3ee6ff', .26); scene.add(diffL)
// voice rings from your head (hi) and the echo: friend's voice out of your speaker, cut before your mic
const rings = Array.from({ length: 4 }, () => { const r = new THREE.Mesh(new THREE.TorusGeometry(.3, .012, 8, 48), new THREE.MeshBasicMaterial({ color: CYAN, transparent: true, toneMapped: false, depthWrite: false })); scene.add(r); return r })
const hiL = label('HI!', '#3ee6ff', .36); scene.add(hiL)
const echoX = label('✕ ECHO', '#ff6159', .3); scene.add(echoX)
// the stream packet and its three copies
const box = () => new THREE.Mesh(new RoundedBoxGeometry(.3, .3, .3, 3, .05), new THREE.MeshStandardMaterial({ color: 0x0d2a33, emissive: CYAN, emissiveIntensity: .8 }))
const pkt = box(); pkt.name = 'stream packet'; scene.add(pkt)
const copies = friends.map((_, i) => { const m = box(); m.material.emissive.setHex(GREEN); m.name = 'copy ' + (i + 1); scene.add(m); return m })
const syncL = friends.map(() => { const l = label('▶ IN SYNC', '#7dffa8', .22); scene.add(l); return l })

// ---------- camera ----------
const over = (d, h) => YOU.g.localToWorld(V(.9, h, 1.9 + d))                                        // over your right shoulder
function shot(n, s, d) {
  switch (n) {
    case 'hi': { const k = inout(p(s, 1.0, d)); return [V().lerpVectors(YOU_HEAD.clone().add(V(2.7, .35, .5)), over(0, 2.5), k), V().lerpVectors(YOU_HEAD.clone().add(V(.45, -.1, -.35)), YOU.lap.localToWorld(V(0, .4, -.4)), k)] }
    case 'camera': return [OUT.clone().add(V(1.6 - s * .08, .3, 4.3)), OUT.clone().add(V(0, .05, 0))]
    case 'squeeze': return [OUT.clone().add(V(1.1, .3, 2.3 - s * .08)), OUT.clone()]
    case 'echo': return [over(.4, 2.6), YOU.lap.localToWorld(V(0, .35, -.3))]
    case 'server': return [V(4.6 - s * .2, 8.5, 11.5), V(.4, 2.2, -2.0)]
    case 'arrive': return [V(-.5 + s * .2, 5.0, 4.5), V(0, 1.8, -5.6)]
    default: { const a = .3 + s * .07; return [V(Math.sin(a) * 13, 9.5, Math.cos(a) * 13 - 1.0), V(0, 2.0, -1.4)] }
  }
}

// ---------- per frame ----------
function update(t, n, s, d, cam, L) {
  const talkYou = n === 'hi' && s < 1.4
  YOU.headG.position.y = 1.72 + (talkYou ? Math.sin(t * 14) * .012 : 0)
  drawYouScreen(n === 'echo' ? 1 : talkYou ? -1 : -2)
  friends.forEach((f, i) => { drawFriendScreen(f, n === 'arrive' && s > .4 + i * .15 || n === 'outro' || n === 'cta'); f.headG.rotation.z = n === 'arrive' ? Math.sin(t * 3 + i) * .08 : 0 })
  YOU.lens.material.color.setHex(['camera', 'squeeze'].includes(n) ? RED : GREEN)
  for (const { led, u, l } of leds) led.visible = hash(u * 3 + l, Math.floor(t * (n === 'server' ? 18 : 6))) > (n === 'server' ? .25 : .45)
  // hi: rings out of your head
  rings.forEach((r, i) => { const k = ((Math.max(s, 0) * 1.2 + i * .25) % 1), on = n === 'hi' && s < 2.2
    r.visible = on; if (!on) return; r.position.copy(YOU_HEAD).add(V(0, 0, -.35 - k * .5)); r.scale.setScalar(.6 + k * 1.6); r.material.opacity = (1 - k) * .8; r.material.color.setHex(CYAN); r.rotation.set(0, YOU.g.rotation.y, 0) })
  hiL.visible = n === 'hi' && s < 2.4; hiL.position.copy(YOU_HEAD).add(V(.5, .7, -.3)); hiL.scale.set(1.44 * back(p(s, 0, .3)) + .001, .36 * back(p(s, 0, .3)) + .001, 1)
  // camera: 6 photos fly out of the lens one after another and line up in the air
  cards.forEach((c, i) => {
    const k = n === 'camera' ? ease(p(s, .4 + i * .18, .9 + i * .18)) : 0, on = n === 'camera' && s > .4 + i * .18
    c.visible = on; if (!on) return
    const end = OUT.clone().add(V(((i % 3) - 1) * .56, (i < 3 ? .2 : -.2), 0))   // a 3x2 grid with gaps: no photo touches another
    c.position.copy(LENS).lerp(OUT, .35).lerp(end, k); c.scale.setScalar((.05 + .95 * k) * .72); c.quaternion.copy(cam.quaternion)   // born just above the lens, never inside the lid
  })
  rateL.visible = n === 'camera' && s > 1.0; rateL.position.copy(OUT).add(V(0, .62, 0))
  // squeeze: one photo shrinks to only the changed part
  const sq = n === 'squeeze' ? ease(p(s, .7, 1.6)) : 0
  slim.visible = n === 'squeeze'; if (slim.visible) { slim.position.copy(OUT); slim.lookAt(cam.position); slim.material[4] = sq > .5 ? diffMat : cardMat; slim.scale.set(1 + .9 * back(p(s, 0, .4)) - sq * .4, 1 + .9 * back(p(s, 0, .4)) - sq * .4, 1) }
  diffL.visible = n === 'squeeze' && s > 1.4; diffL.position.copy(OUT).add(V(0, .7, 0))
  // echo: friend's voice (green) leaves your speaker; the part heading back into your mic is cut
  const ek = n === 'echo' ? s : 0
  if (n === 'echo') rings.forEach((r, i) => { const k = ((ek * 1.1 + i * .25) % 1); r.visible = ek > .3 && ek < 3.2; r.position.copy(YOU.lap.localToWorld(V(0, .1, -.1))).add(V(0, .05 + k * .35, 0)); r.rotation.set(Math.PI / 2, 0, 0); r.scale.setScalar(.6 + k * 1.2); r.material.color.setHex(k > .6 && ek > 1.4 ? RED : GREEN); r.material.opacity = (1 - k) * .9 })
  echoX.visible = n === 'echo' && ek > 1.5; echoX.position.copy(YOU.lap.localToWorld(V(.25, .82, -.35))); echoX.scale.set(1.2 * back(p(ek, 1.5, 1.8)) + .001, .3 * back(p(ek, 1.5, 1.8)) + .001, 1)
  // server: your stream to the server, then a copy to each friend
  tubes[0].material.opacity = ['server', 'arrive'].includes(n) ? .4 : 0; tubes.slice(1).forEach(m => m.material.opacity = n === 'server' && s > 1.2 || n === 'arrive' ? .4 : 0)
  const pk = n === 'server' ? inout(p(s, .1, 1.2)) : 0
  pkt.visible = n === 'server' && pk < .97; pkt.position.copy(toServer.getPoint(pk)); pkt.rotation.set(t, t * 1.3, 0); pkt.scale.setScalar(back(p(s, .1, .35)) * (1 - p(pk, .85, .97)) + .001)
  copies.forEach((c, i) => { const k = n === 'server' ? inout(p(s, 1.3 + i * .12, d - .1)) : 0; c.visible = n === 'server' && s > 1.3 + i * .12 && k < .97
    c.position.copy(fanout[i].getPoint(k)); c.rotation.set(t, t * 1.2, 0); c.scale.setScalar(back(p(s, 1.3 + i * .12, 1.55 + i * .12)) * (1 - p(k, .85, .97)) + .001) })
  syncL.forEach((l, i) => { l.visible = n === 'arrive' && s > .5 + i * .15; l.position.copy(friends[i].headG.getWorldPosition(V(0, 0, 0))).add(V(0, .65, 0)) })
}
const movers = [...cards, slim, pkt, ...copies]
return { movers, solids: [YOU.g, ...friends.map(f => f.g), rack], note: 'VALUES ILLUSTRATIVE',
  steps: [['CAMERA', 'camera'], ['SQUEEZE', 'squeeze'], ['ECHO', 'echo'], ['SERVER', 'server'], ['SYNC', 'arrive']], shot, update }
}
