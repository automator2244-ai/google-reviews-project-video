#!/usr/bin/env bash
# Joins the animation and the end card into out/final-vet.mp4. The animation's music fades out before the card.
set -euo pipefail
cd "$(dirname "$0")"
A=out/google-reviews-vet-full.mp4 B=out/outro.mp4
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$A")
FADE=$(awk "BEGIN{print $D - 0.7}")
ffmpeg -hide_banner -loglevel error -y -i "$A" -i "$B" -filter_complex \
  "[0:v]fps=30,format=yuv420p,setsar=1[v0];[1:v]fps=30,format=yuv420p,setsar=1[v1];
   [0:a]aformat=sample_fmts=fltp:channel_layouts=stereo,aresample=48000,afade=t=out:st=$FADE:d=0.7[a0];
   [1:a]aformat=sample_fmts=fltp:channel_layouts=stereo,aresample=48000[a1];
   [v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart out/final-vet.mp4
echo "out/final-vet.mp4: $(ffprobe -v error -show_entries format=duration -of csv=p=0 out/final-vet.mp4) seconds"
