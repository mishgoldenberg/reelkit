# sh mag/run.sh <id> <out-name>  -> out/{instagram,youtube,upload}/<out-name>.mp4   (voice: sh voice/voice.sh mag-<id>)
set -e
KEEP=${KEEP_FRAMES:-0}; args=; for a in "$@"; do if [ "$a" = --keep-frames ]; then KEEP=1; else args="$args $a"; fi; done; set -- $args
id=$1; name=$2
FF=${FFMPEG:-ffmpeg}; FP=${FFPROBE:-ffprobe}
D=${OUTDIR:-out}; mkdir -p "$D/instagram" "$D/youtube" "$D/upload"
python mag/build.py $id
pre=$(HTML=mag.html CFG=$id OUT=hw-mpre ONLY=0 PORT=9439 node rk.mjs | grep "^layout:")
[ "$pre" = "layout: []" ] || { echo "LAYOUT ISSUES: $pre"; exit 1; }
total=$(node -e "const s=require('fs').readFileSync('mag/$id.timing.js','utf8');console.log(Math.round(JSON.parse(s.slice(s.indexOf('{'))).end*30))")
out=hw-m$id-$(date +%H%M%S); q=$(( (total + 3) / 4 ))
for k in 0 1 2 3; do HTML=mag.html CFG=$id OUT=$out FROM=$((k*q)) TO=$(( (k+1)*q < total ? (k+1)*q : total )) PORT=$((9440+k)) node rk.mjs & done
wait
[ "$(ls $out | wc -l)" = "$total" ] || { echo "only $(ls $out | wc -l) of $total frames rendered, not encoding (frames kept in $out)"; exit 1; }
$FF -v error -y -framerate 30 -i $out/%05d.png -i mag/$id.raw.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -profile:v high -c:a aac -b:a 192k -ar 48000 -ac 2 -shortest -movflags +faststart "$D/instagram/$name.mp4"
cp "$D/instagram/$name.mp4" "$D/youtube/$name.mp4"
d=$($FP -v error -show_entries format=duration -of csv=p=0 "$D/instagram/$name.mp4"); vb=$(python -c "print(int((9.3*8*1024*1024/$d - 140000)))")
$FF -v error -y -i "$D/instagram/$name.mp4" -c:v libx264 -preset slow -b:v $vb -pass 1 -passlogfile $D/upload/pl -an -f null -
$FF -v error -y -i "$D/instagram/$name.mp4" -c:v libx264 -preset slow -b:v $vb -pass 2 -passlogfile $D/upload/pl -pix_fmt yuv420p -profile:v high -c:a aac -b:a 128k -movflags +faststart "$D/upload/$name.mp4"
echo "frames $(ls $out | wc -l) of $total -> $D/instagram/$name.mp4 (${d}s, upload $(stat -c %s $D/upload/$name.mp4) bytes)"
[ "$KEEP" = 1 ] || node rkclean.mjs frames $out hw-mpre --require "$D/instagram/$name.mp4"
