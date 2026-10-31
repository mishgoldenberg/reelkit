# python loud.py <file.mp4> [...]  ->  measures each file's loudness and corrects it in place to -14 LUFS (Instagram's level),
# never letting the true peak go above -1 dBTP. The picture is copied untouched; only the audio is re-encoded.
# Single-pass loudnorm inside the render lands anywhere from -15.5 to -13.9, this makes every reel the same.
import os, re, subprocess, sys

FF = os.environ.get('FFMPEG', 'ffmpeg')
TARGET, CEIL = -14.0, -1.0

def measure(f):
    err = subprocess.run([FF, '-hide_banner', '-nostats', '-i', f, '-af', 'ebur128=peak=true', '-vn', '-f', 'null', '-'], capture_output=True, text=True).stderr
    tail = err[err.rfind('Summary:'):]
    i = float(re.search(r'I:\s+(-?[\d.]+) LUFS', tail)[1]); tp = float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', tail)[1])
    return i, tp

for f in sys.argv[1:]:
    i, tp = measure(f)
    gain = TARGET - i
    if abs(gain) < .3: print(f'{os.path.basename(f)}: {i:.1f} LUFS, ok'); continue
    # short peaks (quiz ticks and chimes) would clip at the full gain: a limiter shaves just those to -1 dB
    lim = tp + gain > CEIL
    af = f'volume={gain:.2f}dB' + (f',alimiter=limit={10 ** (CEIL / 20):.3f}:level=false:attack=2:release=60' if lim else '')
    tmp = f + '.loud.mp4'
    br = '128k' if 'upload' in f.replace('\\', '/').split('/') else '192k'   # upload copies must stay under 10 MB
    subprocess.run([FF, '-v', 'error', '-y', '-i', f, '-c:v', 'copy', '-af', af, '-c:a', 'aac', '-b:a', br, '-ar', '48000', '-ac', '2',
                    '-movflags', '+faststart', tmp], check=True)
    os.replace(tmp, f)
    print(f'{os.path.basename(f)}: {i:.1f} -> {measure(f)[0]:.1f} LUFS (gain {gain:+.1f} dB{", limited" if lim else ""}, peak was {tp:.1f})')
