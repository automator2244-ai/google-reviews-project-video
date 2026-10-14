# סרטון ביקורות למרפאות, גרסה 2

אנימציה אנכית (1080x1920, 30fps, 55 שניות) בעברית, בשפת העיצוב של EZ.Path.AI, ב-[HyperFrames](https://github.com/heygen-com/hyperframes). אחיד לכל המרפאות. `video-links/scripts/publish.sh` מחבר אותה להקלטה האישית ולכרטיס הסיום.

| קובץ | מה זה |
|---|---|
| `out/google-reviews-v2-full.mp4` | האנימציה |
| `out/outro.mp4` | כרטיס הסיום (4.6 שניות), בא אחרי ההקלטה האישית |

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
