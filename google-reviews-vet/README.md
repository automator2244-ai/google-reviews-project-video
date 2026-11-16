# סרטון ביקורות למרפאות וטרינריות

גרסת הווטרינרים של `google-reviews-v2`: אותה אנימציה (1080x1920, 30fps) בשפת העיצוב של EZ.Path.AI, עם טקסטים, שמות ותמונות שמתאימים לווטרינרים. בלי הקלטה אישית של בניה: האנימציה (47 שניות) ואחריה כרטיס הסיום (7 שניות).

| קובץ | מה זה |
|---|---|
| `out/google-reviews-vet-full.mp4` | האנימציה |
| `out/outro.mp4` | כרטיס הסיום (זהה לזה של `google-reviews-v2`) |
| `out/final-vet.mp4` | הסרטון המוכן: אנימציה וכרטיס סיום. זה הקובץ שעולה כ-`vet-v1` |

## מה שונה מהסרטון של המרפאות

- חיפוש "וטרינר קרוב אליי", ושלוש מרפאות בדויות: הדר, גל ו"זנב שמח" (עם סמל של כף רגל).
- סצנה 2: במקום שני הנתונים של Press Ganey (סקר של מטופלים, לא רלוונטי לווטרינרים) יש תמונות של כלב ושל חתול ושני משפטים, בלי מספרים. לא נמצא נתון אמין על בחירת וטרינר לפי ביקורות, ולכן אין נתון.
- מסך הנעילה בטלפון עם תמונת כלב.
- "לקוחות" במקום "מטופלים", "איך היה הביקור?" במקום "איך היה הטיפול?".
- אין סצנת "רגע, כמה מילים ממני", כי אין הקלטה אישית אחריה.

## הפקה מחדש

```bash
cd google-reviews-vet
npx hyperframes@0.8.140 check
npx hyperframes@0.8.140 render -q delivery -o out/google-reviews-vet-full.mp4
npx hyperframes@0.8.140 render -c cards/outro.html -q delivery -o out/outro.mp4
./join.sh        # out/final-vet.mp4
```

## העלאה וקישורים

```bash
cd ../video-links
scripts/publish-shared.sh vet-v1 ../google-reviews-vet/out/final-vet.mp4 --thumb-at 7
#   מריצים את out/shared-vet-v1/register.sql על D1, ואז:
scripts/publish-shared.sh vet-v1 --upload
# קישור לעסק (רק כשבניה אומר למי):
scripts/publish.sh --shared vet-v1 --segment vet --name "..." --phone 05...
```

`--segment vet` שם את הנמען בדשבורד של הווטרינרים: https://go.ezpath-ai.com/admin/vet
