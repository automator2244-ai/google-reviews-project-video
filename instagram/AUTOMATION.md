# אוטומציה: הפקה שבועית, אישור ופרסום

הקובץ הזה הוא ההוראות לסשנים שנפתחים לבד (משימות מתוזמנות). כל סשן כזה מתחיל מאפס, אז הוא קורא קודם את `CLAUDE.md` של הריפו, את `instagram/PLAN.md` ואת `instagram/CONTENT.md`, ורק אז את הסעיף שלו כאן.

**כללי ברזל:**
- **פוסט עולה רק אם ב-`meta.json` שלו `"status": "approved"`.** אף פעם לא מפרסמים טיוטה, ואף פעם לא מסמנים `approved` בלי שבניה כתב "מאשר" בשיחה.
- אף פעם לא מקף ארוך. אף פעם לא מעלים את מדיניות גוגל על סינון ביקורות.
- לא ממציאים נתונים. נתון שלא אומת לא נכנס.
- הכול בשעון ישראל (`Asia/Jerusalem`).
- כל טענה על המוצר חייבת להתאים ל-`instagram/PRODUCT.md`.

## המשימות המתוזמנות

כולן רצות בתוך השיחה המקורית עם בניה (`session_01DGyQqPfkBFmeRzJbnV2P81`), כי רק בה מחובר Composio. **לא לארכב את השיחה הזו.**

| משימה | מתי (שעון ישראל) | מזהה |
|---|---|---|
| פרסום בוקר | א' עד ו', 8:27 | `trig_015F7Qd27kjwZW6EXaZxuyea` |
| פרסום ערב | א' עד ה', 21:27 | `trig_01XxsLhaQM1xFLTespLUE5nF` |
| פרסום מוצאי שבת | שבת, 21:57 | `trig_018CwJty4xd1XMiwHNg5qGbU` |
| הפקה שבועית | א', 4:27 | `trig_01XnR275ewBJYoyg3WvSz47F` |

כל משימה מכבה את עצמה אחרי 4.12.2026.

## סרטונים של בניה

התסריטים ב-`bnaya/SCRIPTS.md` (וגם בדף https://claude.ai/artifact/MChRxZQZFUvqpoPGmEzMw2). כשבניה שולח סרטון: מתמללים (faster-whisper עם המודל `ivrit-ai/whisper-large-v3-turbo-ct2`), מוסיפים כתוביות בשפת העיצוב, מוזיקה רגועה ברקע (מצב `calm`) וכרטיס סיום, ושמים בתור של המשבצת שלו כטיוטה לאישור. אם לא הגיע סרטון עד ההפקה של אותו שבוע, מפיקים את הגיבוי המונפש שבלוח.

## פרטים קבועים

- חשבון: `@ez.path.ai`, מזהה אינסטגרם `17841436299603193`. חיבור: Composio (toolkit `instagram`).
- הענף הראשי של הריפו: `claude/new-session-86yt7m`. המדיה מתפרסמת מקישור ציבורי של GitHub:
  `https://raw.githubusercontent.com/automator2244-ai/google-reviews-project-video/claude/new-session-86yt7m/instagram/queue/<תיקייה>/<קובץ>`
  לכן **קבצי פוסט חייבים להיות ממוזגים לענף הראשי לפני שעת הפרסום.**
- תיקיית פוסט: `instagram/queue/YYYY-MM-DD-HHMM/` (למשל `2026-10-27-2130`). בתוכה `meta.json`, `caption.txt`, ו-`reel.mp4` (ריל) או `slide-01.jpg` ואילך (קרוסלה).
- דף האישור: https://claude.ai/artifact/3YQiEMfTacEvs3u3wJx1zR. המקור שלו: `instagram/review/index.html`. מעדכנים אותו עם `url` הזה (קודם `read`), כדי שהקישור לא ישתנה.

## 1. הפקה שבועית (כל יום ראשון בבוקר)

מכינים את כל הפוסטים של **השבוע הבא** (מיום ראשון הבא ועד מוצאי שבת שאחריו), לפי `PLAN.md`.

1. מצרפים את הריפו (`add_repo`, גישת push), משכפלים, ועובדים על ענף חדש.
2. `npm` ו-`npx` כבר זמינים. מוזיקה: `tools/reel.py` מוריד לבד מ-FreePD מה שחסר.
3. לכל שורה בלוח של השבוע הבא:
   - קרוסלה: כותבים `slides.json` ומריצים `python3 tools/carousel.py queue/<תיקייה>` (יוצא PNG ו-JPG).
   - ריל: כותבים `reel.json` ומריצים `python3 tools/reel.py queue/<תיקייה>`. המוזיקה והסגנון נבחרים לבד לפי הסדרה, בלי חזרה על שיר בתוך 10 ריילס (`music-log.json`).
   - כותבים `caption.txt` לפי הכללים ב-`CONTENT.md`, ו-`meta.json` עם `"status": "draft"`.
4. **סבב ביקורת 1:** מחלצים פריימים (ריל) או מסתכלים על השקפים. בודקים: ההוק נראה בפריים הראשון, רעיון אחד, אין שורה עם מילה בודדת, אין היפוך כיוון בשורה שמתחילה באנגלית, הטקסט בתוך האזור הבטוח, הנתון מאומת ועוד לא שומש. מתקנים ומרנדרים שוב.
5. **סבב ביקורת 2:** מסתכלים שוב על התוצאה הסופית וקוראים את הכיתוב בקול. משפרים.
6. מוסיפים את הפוסטים לדף האישור (`review/index.html`, מערך `POSTS`) ומפרסמים אותו מחדש לאותו קישור, עם הקבצים.
7. Commit, ו-Pull Request לענף הראשי עם מיזוג (בניה אישר מיזוג אוטומטי של תיקיית `instagram/`).
8. ההודעה האחרונה בסשן היא לבניה: קישור לדף האישור, רשימת הפוסטים, ומה בדיוק לענות ("מאשר", או מה לשנות).

**כשבניה עונה באותו סשן:**
- "מאשר": משנים `status` ל-`approved` בכל הפוסטים של השבוע, מעדכנים את דף האישור, commit, PR ומיזוג.
- בקשת שינוי: מתקנים, מרנדרים, מעדכנים את הדף, ושואלים שוב. פוסט שלא אושר נשאר `draft` ולא עולה.

## 2. פרסום (בכל שעת פרסום)

1. מצרפים ומשכפלים את הריפו (הענף הראשי). מחשבים את התיקייה לפי התאריך והשעה בישראל: 8:30 → `HHMM=0830`, 21:30 → `2130`, מוצאי שבת → `2200`.
2. אם אין תיקייה, או שהסטטוס לא `approved`, או שכבר `published`: **לא עושים כלום**, ומסיימים בשורה אחת שמסבירה למה.
3. מוודאים שהקבצים זמינים בקישור הציבורי (`curl -sI` מחזיר 200).
4. מפרסמים דרך Composio, ב-`COMPOSIO_REMOTE_WORKBENCH` עם `proxy_execute`, כדי שהכיתוב יישלח בגוף JSON (ההאשטאגים נשמרים). הקוד:

```python
import time, json
IG = "17841436299603193"
BASE = "https://raw.githubusercontent.com/automator2244-ai/google-reviews-project-video/claude/new-session-86yt7m/instagram/queue/" + SLOT + "/"
CAPTION = """<התוכן של caption.txt, בדיוק>"""

def post(path, body):
    res, err = proxy_execute("POST", path, "instagram", body=body)
    if err: raise RuntimeError(err)
    return res

def wait(cid, limit=300):
    for _ in range(limit // 5):
        st, err = proxy_execute("GET", f"/{cid}", "instagram", query_params={"fields": "status_code,status"})
        if st and st.get("status_code") == "FINISHED": return
        if st and st.get("status_code") == "ERROR": raise RuntimeError(st)
        time.sleep(5)
    raise RuntimeError("container not ready")

if FORMAT == "reel":
    c = post(f"/{IG}/media", {"media_type": "REELS", "video_url": BASE + "reel.mp4", "caption": CAPTION, "share_to_feed": True})
else:
    kids = [post(f"/{IG}/media", {"image_url": BASE + f"slide-{i:02d}.jpg", "is_carousel_item": True})["id"] for i in range(1, N + 1)]
    for k in kids: wait(k, 60)
    c = post(f"/{IG}/media", {"media_type": "CAROUSEL", "children": ",".join(kids), "caption": CAPTION})
wait(c["id"])
pub = post(f"/{IG}/media_publish", {"creation_id": c["id"]})
info, _ = proxy_execute("GET", f"/{pub['id']}", "instagram", query_params={"fields": "id,permalink,caption,timestamp"})
print(json.dumps(info, ensure_ascii=False))
```

5. **בודקים שהכיתוב שחזר זהה ל-`caption.txt`** (כולל ההאשטאגים). אם לא, אומרים לבניה מיד ומצרפים את הכיתוב הנכון להדבקה ידנית.
6. מעדכנים: ב-`meta.json` `"status": "published"`, `"permalink"`, `"media_id"`, `"published_at"`. ב-`CONTENT.md` מוסיפים שורה לטבלת "מה כבר פורסם", ונתונים חדשים לטבלת "נתונים שכבר שומשו". Commit, PR ומיזוג.
7. אם הפרסום נכשל: לא מנסים יותר מפעם אחת נוספת. כותבים לבניה מה נכשל, עם השגיאה.

## 3. מדידה (כל יום ראשון, לפני ההפקה)

מושכים לכל פוסט מהשבוע שעבר: צפיות, שמירות, שיתופים ותגובות (`GET /{media_id}/insights` או `INSTAGRAM_GET_IG_MEDIA_INSIGHTS`). כותבים סיכום קצר ב-`instagram/insights/weekly-YYYY-MM-DD.md`: מה עבד, מה לא, ומה משנים בלוח של השבוע הבא. אם יש פחות מ-10 פוסטים, אומרים שאין עדיין מספיק נתונים למסקנות.
