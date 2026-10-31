# sh cgi/run.sh <id> <out-name> [samples]  ->  photoreal reel: Blender/Cycles frames (cgi/<id>.py) + the 2D overlay
# (show3d.html?overlay=1 on a transparent page) + the voice, into out/{instagram,youtube,upload}/<out-name>.mp4
# Needs Blender (BLENDER=<path to blender>, default: blender on the PATH) and the models listed in models/CREDITS.txt.
set -e
id=$1; name=$2; samples=${3:-48}
FF=${FFMPEG:-ffmpeg}; FP=${FFPROBE:-ffprobe}; BL=${BLENDER:-blender}
D=${OUTDIR:-out}; mkdir -p "$D/instagram" "$D/youtube" "$D/upload"
case $id in faceid) blend=models/marble_bust_01/marble_bust_01_2k.blend ;; ask|ocean) blend=--factory-startup ;; *) echo "no blend for $id"; exit 1 ;; esac
python show/build.py $id
total=$(node -e "const s=require('fs').readFileSync('show/$id.timing.js','utf8');console.log(Math.round(JSON.parse(s.slice(s.indexOf('{'))).end*30))")
cg=cgi-$id-frames; ov=cgi-$id-overlay; mkdir -p $cg $ov; CGABS="$(cd $cg && { pwd -W 2>/dev/null || pwd; })"   # Blender needs an absolute output folder (Windows path under Git Bash)
# 1) CGI frames (skips frames already rendered, so a stopped run can resume)
missing=$(python -c "import os;print(','.join(str(i) for i in range($total) if not os.path.exists('$cg/%05d.png'%(i+1))))")
if [ -n "$missing" ]; then
  first=${missing%%,*}; "$BL" -b $blend --python cgi/$id.py -- "$CGABS" frames=$first-$((total-1)) samples=$samples 2>&1 | grep -E "FRAMING|Error|Traceback" || true
fi
[ "$(ls $cg | wc -l)" -ge "$total" ] || { echo "only $(ls $cg | wc -l) of $total CGI frames"; exit 1; }
# 2) overlay frames, transparent
q=$(( (total + 3) / 4 ))
for k in 0 1 2 3; do HTML=show3d.html CFG=$id QS=overlay=1 TRANSPARENT=1 OUT=$ov FROM=$((k*q)) TO=$(( (k+1)*q < total ? (k+1)*q : total )) PORT=$((9460+k)) node rk.mjs > /dev/null & done
wait
[ "$(ls $ov | wc -l)" = "$total" ] || { echo "only $(ls $ov | wc -l) of $total overlay frames"; exit 1; }
# 3) composite + voice
$FF -v error -y -framerate 30 -i $cg/%05d.png -framerate 30 -i $ov/%05d.png -i show/$id.raw.wav -filter_complex "[0][1]overlay=format=auto" -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -profile:v high -c:a aac -b:a 192k -ar 48000 -ac 2 -shortest -movflags +faststart "$D/instagram/$name.mp4"
cp "$D/instagram/$name.mp4" "$D/youtube/$name.mp4"
d=$($FP -v error -show_entries format=duration -of csv=p=0 "$D/instagram/$name.mp4"); vb=$(python -c "print(int((9.3*8*1024*1024/$d - 140000)))")
$FF -v error -y -i "$D/instagram/$name.mp4" -c:v libx264 -preset slow -b:v $vb -pass 1 -passlogfile $D/upload/pl -an -f null -
$FF -v error -y -i "$D/instagram/$name.mp4" -c:v libx264 -preset slow -b:v $vb -pass 2 -passlogfile $D/upload/pl -pix_fmt yuv420p -profile:v high -c:a aac -b:a 128k -movflags +faststart "$D/upload/$name.mp4"
python loud.py "$D/instagram/$name.mp4" "$D/upload/$name.mp4"
echo "done $name: $total frames, ${d}s"
