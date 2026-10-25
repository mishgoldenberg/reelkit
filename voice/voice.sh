# sh voice/voice.sh <name>...  -> quiz/vo/<name>/<i>.wav (48 kHz mono) for every <i>.txt, then a Whisper word check
# Voice: Kokoro-82M "af_heart" (the female narrator for every reel). VOICE=<kokoro voice> picks another.
set -e
VC=voice; VP=${WHISPER_PY:-python}; KP=${KOKORO_PY:-python}   # Python envs with faster-whisper / kokoro installed
FF=${FFMPEG:-ffmpeg}
VOICE=${VOICE:-af_heart}
for z in "$@"; do
  d=quiz/vo/$z; n=$(ls $d/*.txt | wc -l)
  $KP $VC/kokoro_tts.py $VOICE $d $n > /dev/null
  # Kokoro: trim the edges (pauses between sentences stay) and speed up 1.1x, like every reel so far
  af="-af silenceremove=start_periods=1:start_threshold=-55dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse,atempo=1.1"
  for ((i=0;i<n;i++)); do $FF -v error -y -i $d/$i.cb.wav $af -ar 48000 -ac 1 -c:a pcm_s16le $d/$i.wav; done
  echo "== $z"; $VP $VC/asrcheck.py $d $n 2>/dev/null
done
