# סרטון: ביקורות בגוגל למרפאות שיניים

סרטון אנימציה אנכי (1080x1920, 30fps, 55 שניות) בעברית, בנוי ב-[HyperFrames](https://github.com/heygen-com/hyperframes). המסמך המקורי עם התסריט והכללים: `../docs/video-brief.md`.

## הקבצים המוכנים

| קובץ | מה זה |
|---|---|
| `out/google-reviews-demo-full.mp4` | איכות מלאה |
| `out/google-reviews-demo-whatsapp.mp4` | גרסה דחוסה (עד 16MB) לשליחה ישירה בוואטסאפ |

## מבנה

```
google-reviews-demo/
├── index.html        כל 8 הסצנות, הכתוביות, האודיו וציר הזמן
├── BRIEF.md          תקציר הכוונה
├── STORYBOARD.md     הסצנות והזמנים כפי שנבנו
├── CREDITS.md        מקור ורישיון של המוזיקה, הגופן, האימוג'י והאייקונים
├── assets/
│   ├── audio/        מוזיקת רקע וצלילי לחיצה
│   ├── fonts/        Heebo, קבצים מקומיים
│   ├── emoji/        👋 ו-🙏 כקובצי SVG
│   ├── icons/        רישיון האייקונים
│   └── vendor/       GSAP מקומי (בלי תלות ברשת בזמן ההפקה)
└── out/              קובצי ה-MP4
```

## הפקה מחדש

דרישות: Node.js 22 ומעלה ו-FFmpeg.

```bash
cd google-reviews-demo
npx hyperframes@0.8.140 check                      # בדיקות
npx hyperframes@0.8.140 render -q delivery -o out/google-reviews-demo-full.mp4
```

### שם העסק ופרטי הקשר בסיום

הסיום מציג את EZ.Path.AI ואת 055-271-6456 (ברירת המחדל ב-`index.html`). אפשר להחליף אותם בהפקה:

```bash
npx hyperframes@0.8.140 render -q delivery -o out/google-reviews-demo-full.mp4 \
  --variables '{"businessName":"EZ.Path.AI","contact":"055-271-6456"}'
```

### גרסה דחוסה לוואטסאפ

```bash
ffmpeg -y -i out/google-reviews-demo-full.mp4 -c:v libx264 -profile:v high -pix_fmt yuv420p \
  -b:v 1800k -maxrate 2400k -bufsize 4800k -c:a aac -b:a 128k -movflags +faststart \
  out/google-reviews-demo-whatsapp.mp4
```

## אודיו

- רצועה 10: מוזיקת רקע (`assets/audio/music.mp3`), כבר עם כניסה ודעיכה, בעוצמה של כ-מינוס 18 LUFS.
- רצועה 11: צלילי לחיצה ובועות, שקטים מאוד.
- רצועה 12: שמורה לקריינות עתידית. מוסיפים `<audio id="voiceover" src="assets/audio/voiceover.mp3" data-start="0" data-track-index="12">` ב-`index.html`, ואז כדאי להנמיך את המוזיקה (`data-volume` של `#music`).
