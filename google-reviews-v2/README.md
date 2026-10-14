# סרטון ביקורות למרפאות, גרסה 2

אנימציה אנכית (1080x1920, 30fps, 55 שניות) בעברית, בשפת העיצוב של EZ.Path.AI, ב-[HyperFrames](https://github.com/heygen-com/hyperframes). אחיד לכל המרפאות. `video-links/scripts/publish.sh` מחבר אותה להקלטה האישית ולכרטיס הסיום.

| קובץ | מה זה |
|---|---|
| `out/google-reviews-v2-full.mp4` | האנימציה |
| `out/outro.mp4` | כרטיס הסיום (4.6 שניות), בא אחרי ההקלטה האישית |
| `out/instagram-reel.mp4` | רילס לאינסטגרם (34 שניות), מתוך אותן סצנות, עם סיום וטלפון |
| `out/instagram-reel-cover.jpg` | תמונת שער לרילס |

## הפקה מחדש

```bash
cd google-reviews-v2
npx hyperframes@0.8.140 check
npx hyperframes@0.8.140 render -q delivery -o out/google-reviews-v2-full.mp4
npx hyperframes@0.8.140 render -c cards/outro.html -q delivery -o out/outro.mp4
# טלפון אחר בכרטיס הסיום:
npx hyperframes@0.8.140 render -c cards/outro.html -q delivery -o out/outro.mp4 --variables '{"contact":"050-0000000"}'
```

התסריט, הנתונים והמקורות: `BRIEF.md`. הסצנות והזמנים: `STORYBOARD.md`.

## הרילס לאינסטגרם (`reel.html`)

אותן סצנות בסדר אחר: הפער (230 מול 0), החיפוש, הטלפון, המשוב, התוצאה וסיום עם טלפון. הכול מוקטן ל-80% כדי שהכתוביות לא ייפלו מתחת לכפתורים ולכיתוב של אינסטגרם בתחתית המסך. המוזיקה: `assets/audio/music-reel.mp3` (אותו קטע, 40.6 שניות עם דעיכה).

```bash
npx hyperframes@0.8.140 render -c reel.html -q delivery -o out/reel-raw.mp4
ffmpeg -i out/reel-raw.mp4 -filter_complex "[0:v]setpts=PTS/1.2,fps=30[v];[0:a]atempo=1.2[a]" -map "[v]" -map "[a]" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart out/instagram-reel.mp4
```

## סרטוני המחקר

| קובץ | מה זה |
|---|---|
| `out/research-photos-35s.mp4` | "לפני שהם מתקשרים": תמונות אמיתיות ושלושה נתונים (35 שניות) |
| `out/research-illustrated-20s.mp4` | "גוגל אומר את זה בעצמו": איורים ושני נתונים (20 שניות) |
| `out/research-photos-cover.jpg`, `out/research-illustrated-cover.jpg` | תמונות שער |

המקורות ב-`BRIEF.md`, הרישיונות ב-`CREDITS.md`. בלי האצה: הזמנים בקובץ הם הזמנים הסופיים.

```bash
npx hyperframes@0.8.140 render -c research-photos.html -q delivery -o out/rp-raw.mp4
npx hyperframes@0.8.140 render -c research-illustrated.html -q delivery -o out/ri-raw.mp4
# ואז דחיסה: ffmpeg -i out/rp-raw.mp4 -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart out/research-photos-35s.mp4
```
