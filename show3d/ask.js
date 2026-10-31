// ask is rendered in Blender (cgi/ask.py); this stub only gives the overlay its steps and note (show3d.html?overlay=1).
export default async function ({ V }) {
  return { note: 'VALUES ILLUSTRATIVE', steps: [['TOKENS', 'tokens'], ['DATA CENTER', 'datacenter'], ['MATH', 'weights'], ['ATTENTION', 'attention'], ['NEXT WORD', 'predict']],
    shot: () => [V(0, 5, 10), V(0, 0, 0)], update() {} }
}
