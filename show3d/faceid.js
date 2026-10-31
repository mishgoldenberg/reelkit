// faceid is rendered in Blender (cgi/faceid.py); this stub only gives the overlay its steps and note (show3d.html?overlay=1).
export default async function ({ V }) {
  return { note: 'INFRARED SHOWN IN RED · ILLUSTRATION', steps: [['FLOOD', 'flood'], ['DOTS', 'dots'], ['DEPTH', 'depth'], ['MATCH', 'compare'], ['UNLOCK', 'unlock']],
    shot: () => [V(0, 5, 10), V(0, 0, 0)], update() {} }
}
