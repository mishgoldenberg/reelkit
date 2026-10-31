// ocean is rendered in Blender (cgi/ocean.py); this stub only gives the overlay its steps and note (show3d.html?overlay=1).
export default async function ({ V }) {
  return { note: 'LIGHT SHOWN SLOWED · ILLUSTRATION', steps: [['COAST', 'coast'], ['CABLE', 'hose'], ['GLASS', 'cut'], ['LIGHT', 'light'], ['BOOSTER', 'booster']],
    shot: () => [V(0, 5, 10), V(0, 0, 0)], update() {} }
}
