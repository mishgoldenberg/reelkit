---
name: reel
description: Make a vertical Instagram/TikTok reel with reelkit from a one-line idea. Use when the user asks for a reel, short, or quiz video.
---

# Make a reel with reelkit

1. **Pick the format.** An explainer or "N free tools" video -> `mag` (mag/build.py). A quiz -> `quiz` (quiz/build.py).
2. **Write the script** as a new entry in `REELS` (mag) or `QUIZZES` + `SAY` (quiz):
   - 5-8 lines, one idea each. Line 1 is the hook and the cover: a surprising, concrete claim about the viewer's problem.
   - Split each line into short phrases with `|` and put 1-2 key words in `*stars*`.
   - Give every line a presenter `pose` (see the list in robot.js) that matches the words, and a `card` when you have a real
     screenshot (`img`), a short list (`list`) or a message (`toast`) to show.
   - Only state facts you have checked in the source (docs, README, code). End with one honest catch or limit.
3. **Voice it:** `python mag/build.py <id> lines`, then `sh voice/voice.sh mag-<id>`. Every line must score 1.00 in the
   word check; if a word comes out wrong, reword the line or add the word to `LEX` in voice/kokoro_tts.py.
4. **Render:** `sh mag/run.sh <id> <name>` (or `sh quiz/run.sh <id> <name>`). It stops on layout problems; fix the text
   that does not fit and run again.
5. **Check before you hand it over:** look at frames at the start of every line (first frame = the cover) and listen to
   the start of the audio.
