#!/bin/bash
# GTA VI-style teaser de Mark Kaizen (local, ffmpeg). Entradas: hoja de personaje + hero.
set -e
cd "$(dirname "$0")"
SHEET=${SHEET:-/root/.claude/uploads/02b330e5-cc3f-569b-af09-0be7409b6328/41ca21f7-image.png}
HERO=${HERO:-/root/.claude/uploads/02b330e5-cc3f-569b-af09-0be7409b6328/6a09ca98-image.jpg}
W=_w; FPS=30; D=2.2
# paneles de la hoja: nombre x y w h
crop(){ ffmpeg -v error -y -i "$SHEET" -vf "crop=$3:$4:$1:$2" $W/$5.png; }
crop 0 0 775 810 main
crop 782 0 238 362 p1
crop 1026 0 228 362 p2
crop 782 366 238 444 p3
crop 1026 366 228 444 p4
crop 0 822 420 432 b1
crop 424 822 428 432 b2
crop 856 822 398 432 b3
cp "$HERO" $W/hero.png
# cada panel -> clip 1080x1920: fondo desenfocado + primer plano con zoom lento
i=0
for n in main p3 b1 p2 b2 p1 b3 p4 hero; do
  i=$((i+1))
  dir=$([ $((i%2)) -eq 0 ] && echo "1+0.0010*on" || echo "1.18-0.0010*on")
  ffmpeg -v error -y -i $W/$n.png -filter_complex "
   [0:v]split[a][b];
   [a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:5,eq=brightness=-0.15[bg];
   [b]scale=1080:-2:flags=lanczos,format=rgba[fg];
   [bg][fg]overlay=(W-w)/2:(H-h)/2,
   zoompan=z='$dir':d=$(python3 -c "print(int($D*$FPS))"):x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=$FPS,
   colorbalance=rs=.10:gs=-.04:bs=.14:rh=.12:bh=.10,eq=saturation=1.35:contrast=1.08,
   vignette=PI/4,format=yuv420p[v]" -map "[v]" -frames:v $(python3 -c "print(int($D*$FPS))") -r $FPS $W/c$i.mp4
done
# concat con fundido corto
ins=""; for k in $(seq 1 $i); do ins="$ins -i $W/c$k.mp4"; done
fc=""; prev="[0:v]"; off=0
for k in $(seq 1 $((i-1))); do
  off=$(python3 -c "print(round($k*($D-0.25),2))")
  fc="$fc${prev}[$k:v]xfade=transition=fadeblack:duration=0.25:offset=$off[x$k];"; prev="[x$k]"
done
ffmpeg -v error -y $ins -filter_complex "${fc%;}" -map "${prev}" $W/seq.mp4
echo built
