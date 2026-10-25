# reelkit

The code behind the reels on [@mish.builds](https://www.instagram.com/mish.builds/): vertical 1080×1920 videos made from a
script, not edited by hand. You write the lines, it voices them, animates every scene in a headless browser, mixes the
sound and exports an Instagram-ready MP4 (plus a copy under 10 MB for schedulers).

Built to be driven by an AI coding agent: the `.claude/skills/reel` skill tells Claude Code how to make a new reel with it.

## What's in it

| | |
|---|---|
| `mag.html` + `mag/build.py` | "Magazine" reels: the spoken line as the headline (key words in italics), a screenshot or text card, an optional presenter character underneath |
| `quiz.html` + `quiz/build.py` | Rapid-fire quizzes: 4 answer cards, a 3-second ticking timer, the right answer turns green |
| `robot.js` | A talking presenter: whole poses that switch on each phrase, a face drawn live on its screen (blinks, glances, lip-sync to the voice) |
| `rk.mjs` | Frame grabber: renders any page above frame by frame through headless Chrome (DevTools protocol) |
| `voice/` | Narration with [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (pauses between sentences, a pronunciation fix list) and a Whisper check that every word came out right |
| `sfx/cc0/` | Whoosh / pop / tick / blip and a lo-fi loop, all CC0 from Freesound via Openverse (see `CREDITS.txt`) |

## Setup

- Node 18+, Python 3.11+, ffmpeg on your PATH (or set `FFMPEG` / `FFPROBE`), Google Chrome (or set `CHROME`)
- `pip install numpy kokoro soundfile` for the voice, `pip install faster-whisper` for the word check
  (`KOKORO_PY` / `WHISPER_PY` point the scripts at those Python environments if they are separate)

## Make a reel

```bash
python mag/build.py mods3 lines     # writes the script lines to quiz/vo/mag-mods3/*.txt
sh voice/voice.sh mag-mods3          # voices them and checks every word
sh mag/run.sh mods3 my_reel          # renders -> out/instagram/my_reel.mp4 and out/upload/my_reel.mp4
```

New reel: add an entry to `REELS` in `mag/build.py` (phrases split by `|`, accent words in `*stars*`, a pose and a card per
line). Quizzes work the same way with `QUIZZES` / `SAY` in `quiz/build.py` and `sh quiz/run.sh <id> <name>`.

## The presenter

The character images are not in this repo (it's my account's mascot). To use your own: put 1080-friendly PNGs with a
transparent background in `character/` named `blank-<pose>.png` (poses listed at the top of `robot.js`), each with an empty
face area, and describe where that area is in `character/blank.json` (`cx`, `cy`, `w`, `ang` per pose). Without them the
reels render with no presenter.

## License

MIT. The sounds in `sfx/cc0` are CC0 (public domain).
