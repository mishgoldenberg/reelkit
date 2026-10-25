# python asrcheck.py <dir> <n>  -> for each <dir>/<i>.wav: Whisper transcript vs <dir>/<i>.txt, word match ratio
import sys, re, pathlib, difflib
from faster_whisper import WhisperModel

d, n = pathlib.Path(sys.argv[1]), int(sys.argv[2])
m = WhisperModel('small.en', device='cpu', compute_type='int8')
norm = lambda s: re.sub(r"[^a-z0-9 ]", ' ', s.lower().replace('-', ' ')).split()
worst = 1.0
for i in range(n):
    want = (d / f'{i}.txt').read_text(encoding='utf-8')
    segs, _ = m.transcribe(str(d / f'{i}.wav'), language='en', beam_size=5)
    got = ' '.join(s.text for s in segs).strip()
    r = difflib.SequenceMatcher(None, norm(want), norm(got)).ratio()
    worst = min(worst, r)
    print(f'{i} {r:.2f} | {got}', flush=True)
print(f'worst {worst:.2f}')
