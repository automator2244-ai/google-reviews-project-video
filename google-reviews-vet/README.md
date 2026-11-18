# סרטון ביקורות למרפאות וטרינריות

גרסת הווטרינרים של `google-reviews-v2`: אותה אנימציה (1080x1920, 30fps, 52 שניות) בשפת העיצוב של EZ.Path.AI, עם טקסטים, שמות ותמונות שמתאימים לווטרינרים. כמו במרפאות, היא נגמרת ב"רגע, כמה מילים ממני", ואחריה באה ההקלטה האישית של בניה וכרטיס הסיום (`publish.sh`).

| קובץ | מה זה |
|---|---|
| `out/google-reviews-vet-full.mp4` | האנימציה, התבנית של `publish.sh --template` |
| `out/outro.mp4` | כרטיס הסיום (זהה לזה של `google-reviews-v2`) |
| `out/final-vet.mp4` | גרסה ישנה (16.11): בלי הקלטה, עם כרטיס הסיום. עלתה כ-`vet-v1` |

## מה שונה מהסרטון של המרפאות

- חיפוש "וטרינר קרוב אליי", ושלוש מרפאות בדויות: הדר, גל ו"זנב שמח" (עם סמל של כף רגל).
- סצנה 2: במקום שני הנתונים של Press Ganey יש תמונות של כלב ושל חתול ושני משפטים, בלי מספרים.
- 105 לקוחות החודש (בקשת בניה 18.11).
- שני כפתורים בלבד: "היה מעולה, הייתה חוויה טובה" ו"היה פחות טוב.." (בקשת בניה 18.11).
- מסך הנעילה בטלפון עם תמונת כלב. "לקוחות" במקום "מטופלים", "איך היה הביקור?".

## הפקה מחדש

```bash
cd google-reviews-vet
npx hyperframes@0.8.140 check
npx hyperframes@0.8.140 render -q delivery -o out/google-reviews-vet-full.mp4
npx hyperframes@0.8.140 render -c cards/outro.html -q delivery -o out/outro.mp4
./join.sh        # out/final-vet.mp4
```

## קישור לעסק עם הקלטה אישית (הדרך הרגילה)

```bash
cd ../video-links
scripts/publish.sh --name "אבי" --phone 054... --segment vet \
  --template ../google-reviews-vet/out/google-reviews-vet-full.mp4 --template-speed 1.08 --personal /path/to/recording.mp4
#   מריצים את out/<id>/register.sql על D1, ואז:
scripts/upload.sh <id>
```

`--segment vet` שם את הנמען בדשבורד של הווטרינרים: https://go.ezpath-ai.com/admin/vet. אחר כך רושמים את הקישור בעמודה O בגיליון.

נשלחו: אבי, תיבת נח (18.11), https://go.ezpath-ai.com/v/atvefzk9
