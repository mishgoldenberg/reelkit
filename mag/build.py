# python mag/build.py <id> lines  ->  quiz/vo/mag-<id>/<i>.txt   (then: sh quiz/voice.sh mag-<id>)
# python mag/build.py <id>        ->  mag/<id>.timing.js (timeline for mag.html) + mag/<id>.raw.wav (the voice)
# "Magazine" reels: cream page, the spoken phrase as the headline (key words in orange italics), a real screenshot or text card,
# and the talking robot underneath. Script markup: phrases split by "|", accent words in *stars*. The voice reads it plain.
import json, os, re, subprocess, sys, wave, pathlib
import numpy as np

HERE = pathlib.Path(__file__).parent
VO = HERE.parent / 'quiz' / 'vo'
SR, FPS = 48000, 30
FF = os.environ.get('FFMPEG', 'ffmpeg')
GAP, START, TAIL = .25, .15, 1.6

# Facts for 'mods3': github.com/mishgoldenberg/claude-mods README + plugins/*/hooks/register.tsx + mod-manager CATALOG, read Oct 22-25:
# usage-meter: 5-hour and 7-day plan-limit bars, reset countdown, "full in ~X" estimate from this session; zero tokens.
# context-keeper: "What fills it" breakdown; writes a handoff checkpoint, by itself at 85% (before /compact); uses tokens (the note).
# loop-breaker: same command failing 3x in a row (or the same code rewritten 3x in a turn) -> toast
#   "Same command failed 3× in a row: <cmd>" + tells the agent to stop retrying and rethink; zero tokens.
REELS = {
    'mods3': {
        'kicker': 'CLAUDE CODE · FREE MODS',
        'lines': [
            ('Claude Code is quietly | eating your *plan limit.*', {'pose': 'shocked'}),
            ('Here are *three free mods* | that fix it.', {'pose': 'count', 'card': {'type': 'list', 'items': ['usage-meter', 'context-keeper', 'loop-breaker']}}),
            ("One: *usage meter.* | Your five hour and seven day limits, | live, | and when you'll *run out.*",
             {'pose': 'present', 'card': {'type': 'img', 'src': 'mag/img/meter.png', 'label': 'usage-meter'}}),
            ('Two: *context keeper.* | It shows what *fills* your context, | and saves a *checkpoint* | before it compacts.',
             {'pose': 'point-up-left', 'card': {'type': 'img', 'src': 'mag/img/ctx.png', 'label': 'context-keeper'}}),
            ('Three: *loop breaker.* | When your agent fails | the same command *three times,* | it tells it to *stop* | and rethink.',
             {'pose': 'crossed', 'card': {'type': 'toast', 'text': 'Same command failed 3× in a row: npm test', 'label': 'loop-breaker · the warning it shows'}}),
            ('All three are *free* | and open source. | Only context keeper | uses a few *tokens.*', {'pose': 'explain'}),
            ('Follow for more | *free tools* like this. | The repo is in my bio.', {'pose': 'thumbs-up'}),
        ],
    },
}

def plain(s): return re.sub(r'\s+', ' ', s.replace('|', ' ').replace('*', '')).strip()

def readwav(p):
    with wave.open(str(p)) as w: return np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(float) / 32768

SFX = HERE.parent / 'sfx' / 'cc0'                                   # CC0 sounds from Freesound via Openverse (sfx/cc0/CREDITS.txt)
_cache = {}
def load(name):
    if name not in _cache:
        raw = subprocess.run([FF, '-v', 'error', '-i', str(SFX / f'{name}.mp3'), '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
        _cache[name] = np.frombuffer(raw, dtype='<i2').astype(float) / 32768
    return _cache[name]

def put(buf, name, t, gain):
    x = load(name) * gain; i = max(0, int(t * SR)); j = min(len(buf), i + len(x)); buf[i:j] += x[:j - i]

def sfx(lines, n):
    """one small sound per visual event, at the frame mag.html animates it"""
    b = np.zeros(n)
    for k, L in enumerate(lines):
        if k: put(b, 'whoosh', L['t0'] - .12, .22); put(b, 'blip', L['t0'] - .05, .12)      # new headline + robot pose pop
        c = L['scene'].get('card')
        if c: put(b, 'pop', L['t0'] + .16, .4)                                                # card lands
        if c and c['type'] == 'list':
            for i in range(len(c['items'])): put(b, 'tick', L['t0'] + .42 + i * .45, .35)     # each list row
    return b

def music(rms, n, name):
    """quiet lo-fi bed, looped; dips while the voice talks, comes up in the pauses, fades in and out"""
    if not name: return np.zeros(n)
    m = load(name); m = np.tile(m, n // len(m) + 1)[:n]; m = m / (np.abs(m).max() + 1e-9)
    talk = np.repeat(np.convolve((rms > .08).astype(float), np.ones(9) / 9, 'same'), SR // FPS)
    talk = np.pad(talk, (0, max(0, n - len(talk))))[:n]
    g = .13 - .06 * talk
    g *= np.clip(np.arange(n) / (.6 * SR), 0, 1) * np.clip((n - np.arange(n)) / (1.4 * SR), 0, 1)
    return m * g

def build(rid):
    R = REELS[rid]; d = VO / f'mag-{rid}'
    V = [readwav(d / f'{i}.wav') for i in range(len(R['lines']))]
    t, lines = START, []
    for (text, scene), v in zip(R['lines'], V):
        dur = len(v) / SR
        ph = [x.strip() for x in text.split('|')]
        w = np.array([len(x.replace('*', '')) + 4 for x in ph], float); w /= w.sum()
        starts = t + np.concatenate([[0], np.cumsum(w)[:-1]]) * dur
        html = [re.sub(r'\*([^*]+)\*', r'<i>\1</i>', x) for x in ph]
        lines.append({'t0': round(t, 3), 't1': round(t + dur, 3), 'scene': scene, 'phrases': [{'t': round(float(s), 3), 'html': h} for s, h in zip(starts, html)]})
        t += dur + GAP
    end = t - GAP + TAIL
    for i, L in enumerate(lines): L['end'] = lines[i + 1]['t0'] if i + 1 < len(lines) else round(end, 3)
    out = np.zeros(int(end * SR) + 1)
    for L, v in zip(lines, V): i = int(L['t0'] * SR); out[i:i + len(v)] += v
    out = out / (np.abs(out).max() + 1e-9) * .9
    hop = SR // FPS                                                     # loudness per video frame for the robot's mouth (voice only)
    rms = np.array([np.sqrt((out[i:i + hop] ** 2).mean()) for i in range(0, len(out) - hop, hop)])
    mix = out + sfx(lines, len(out)) + music(rms, len(out), R.get('music', 'music'))
    mix = mix / (np.abs(mix).max() + 1e-9) * .9
    with wave.open(str(HERE / f'{rid}.raw.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
    rms = np.convolve(rms, [.25, .5, .25], 'same'); rms = np.clip(rms / (np.percentile(rms[rms > 1e-3], 95) + 1e-9), 0, 1)
    poses = [{'t': 0 if i == 0 else round(L['t0'] - .05, 3), 'pose': L['scene']['pose']} for i, L in enumerate(lines)]
    (HERE / f'{rid}.timing.js').write_text('window.MAG = ' + json.dumps({'end': round(end, 3), 'kicker': R['kicker'], 'lines': lines,
        'poses': poses, 'mouth': [round(float(x), 3) for x in rms]}) + '\n', encoding='utf-8')
    print(f'{rid}: {end:.1f}s, {len(lines)} lines')

if len(sys.argv) > 2 and sys.argv[2] == 'lines':
    d = VO / f'mag-{sys.argv[1]}'; d.mkdir(parents=True, exist_ok=True)
    for i, (text, _) in enumerate(REELS[sys.argv[1]]['lines']): (d / f'{i}.txt').write_text(plain(text), encoding='utf-8')
    print(len(REELS[sys.argv[1]]['lines']), 'lines')
else:
    build(sys.argv[1])
