# python kokoro_tts.py <voice> <out.wav> <text>      one line with a Kokoro-82M voice (24 kHz)
# python kokoro_tts.py <voice> <dir> <n>             <dir>/<i>.cb.wav for each <dir>/<i>.txt (same file names as cbtts.py)
# Voices: af_heart af_bella af_nicole af_sarah af_aoede af_kore (US), bf_emma bf_isabella (UK). Runs in .kokoro (CPU torch).
import re, sys, pathlib
import numpy as np, soundfile as sf
from kokoro import KPipeline

voice = sys.argv[1]
pipe = KPipeline(lang_code=voice[0], repo_id='hexgrad/Kokoro-82M')
# words Kokoro gets wrong -> phonemes (misaki's [word](/ipa/) syntax); the .txt keeps the plain word for the Whisper check
LEX = {'Claude': 'klˈɔːd', 'Where': 'wˈɛɹ', 'mish': 'mˈɪʃ', 'Mish': 'mˈɪʃ'}

# Each sentence is read on its own with a real pause after it ("Scared? <pause> These questions are scarier."), not run together.
GAP = {'?': .5, '!': .4, '.': .32, ':': .22}

def say(text):
    out = []
    for s in re.findall(r'.+?(?:[.?!:](?=\s|$)|$)', text.strip()):
        s = s.strip()
        if not s: continue
        s2 = re.sub(r'\b(' + '|'.join(LEX) + r')\b', lambda m: f'[{m[1]}](/{LEX[m[1]]}/)', s)
        a = np.concatenate([x.numpy() if hasattr(x, 'numpy') else np.asarray(x) for _, _, x in pipe(s2, voice=voice)])
        nz = np.flatnonzero(np.abs(a) > .01)                              # trim the model's own edge silence so the gaps are exact
        if len(nz): a = a[max(0, nz[0] - 240):nz[-1] + 1200]
        out += [a, np.zeros(int(GAP.get(s[-1], 0) * 24000), dtype=a.dtype)]
    return np.concatenate(out[:-1] if len(out) > 1 else out)

if sys.argv[2].endswith('.wav'):
    sf.write(sys.argv[2], say(' '.join(sys.argv[3:])), 24000)
else:
    d = pathlib.Path(sys.argv[2])
    for i in range(int(sys.argv[3])):
        sf.write(str(d / f'{i}.cb.wav'), say((d / f'{i}.txt').read_text(encoding='utf-8').strip()), 24000)
        print('line', i, flush=True)
