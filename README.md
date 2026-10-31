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

## 3D explainers (three.js) and photoreal (Blender)

"What happens when you..." reels: one live number on top (milliseconds, dots, tokens), a 3D world that shows every step as
it is spoken, word-by-word captions and a share card at the end.

| | |
|---|---|
| `show3d.html` | The shared 3D shell: renderer, lights, bloom and depth of field, a scanned parcel and a server rack, plus the 2D layer (counter, step bar, captions, presenter). Every frame is a pure function of time |
| `show3d/<id>.js` | One world per reel: `enter` (pressing Enter on a URL), `tap` (contactless card payment), `cloud` (cloud gaming), `call` (video call). `faceid`, `ask` and `ocean` are stubs that only give the overlay its steps |
| `show/build.py` | The scripts (`REELS`: caption, spoken text, scene, pose, counter value, highlighted words), then the timeline from Whisper word timings and the mixed voice + sound + music |
| `cgi/` | Blender Cycles versions, rendered on the GPU (OptiX, so an NVIDIA card): `faceid` (a scanned marble bust, 30,000 ray-traced dots), `ask` (token tiles, a data-center aisle, a circuit board), `ocean` (seabed, the cable, a shark). `show3d.html?overlay=1` draws the 2D layer on a transparent page to sit on top |
| `loud.py` | Brings finished MP4s to -14 LUFS (Instagram's level) without touching the picture |
| `vendor/three/` | The three.js r180 files `show3d.html` imports (MIT) |

```bash
python show/build.py enter lines    # writes the script lines to quiz/vo/show-enter/*.txt
sh voice/voice.sh show-enter        # voices them and checks every word
sh show/run.sh enter my_reel        # renders in headless Chrome -> out/instagram/my_reel.mp4 and out/upload/my_reel.mp4

sh cgi/run.sh faceid my_reel 48     # photoreal: Blender frames + overlay + voice (48 = Cycles samples; BLENDER=<path> if not on PATH)
```

Same flow for every id. A stopped Blender run resumes where it left off (frames stay in `cgi-<id>-frames/`).
`show/run.sh` stops if a caption does not fit or a moving object touches another (`WORLD.movers` / `WORLD.solids`).

The Blender reels need models that are not in this repo; `models/CREDITS.txt` lists each one with its Poly Haven page
(all CC0) and the folder it goes in. The `ocean` shark is "Rigged Bull Shark" by nerk987 on BlendSwap, **CC-BY 4.0**: download
it yourself into `models/bull_shark/src/BullShark.blend` and credit the author wherever you post the reel. For `faceid`, run
`blender -b models/marble_bust_01/marble_bust_01_2k.blend --python cgi/photo_tex.py` once to make the printed photo.

How they were made: Claude Code wrote the scripts and the 3D scenes, Kokoro voiced them on a home PC, headless Chrome drew
every frame (`rk.mjs`), and Whisper word timings place the captions.

## The presenter

The character images are not in this repo (it's my account's mascot). To use your own: put 1080-friendly PNGs with a
transparent background in `character/` named `blank-<pose>.png` (poses listed at the top of `robot.js`), each with an empty
face area, and describe where that area is in `character/blank.json` (`cx`, `cy`, `w`, `ang` per pose). Without them the
reels render with no presenter.

## License

MIT. The sounds in `sfx/cc0` and the models in `models/` are CC0 (public domain); `vendor/three` is three.js (MIT, its own
`LICENSE`).
