# העלאה מחדש עם מסך ראשון חדש (מוצאי שבת, 14.11.2026)

בניה ביקש (13.11) מסך ראשון שונה ותופס לכל מה שעלה מ-27.10, ובלי תווית הסדרה בפינה. באינסטגרם אי אפשר להחליף וידאו או תמונה של פוסט שכבר עלה, ובחיבור (Composio) אין מחיקה של פוסט. לכן: מעלים מחדש גרסה חדשה של כל פוסט, לפי הסדר המקורי, ובניה מעביר לארכיון את הישנים מהאפליקציה.

## הסדר
1. **לא לפני צאת השבת.** בשבת לא עושים באינסטגרם שום דבר שנראה לציבור (בקשת בניה).
2. בודקים מכסה: `GET /{ig-user-id}/content_publishing_limit` (מגבלה של 50 ב-24 שעות). צריך 33, ועוד הפוסט של 22:00 ושל יום ראשון.
3. יוצרים את כל המכלים (ריל: `video_url`, קרוסלה: ילדים ואז `CAROUSEL`), בקבוצות קטנות, ושומרים את המזהים ב-`/mnt/files/repost.json`. לפני כל ניסיון חוזר בודקים שם מה כבר נוצר או פורסם.
4. מחכים שכולם `FINISHED`.
5. מפרסמים **אחד אחד לפי הסדר בטבלה** (מהישן לחדש), עם הפסקה של כחצי דקה בין פרסום לפרסום, כדי שהגריד ישמור על הסדר ולא ייראה כמו הצפה. אחרי כל פרסום בודקים שהכיתוב זהה ל-`caption.txt`.
6. מעדכנים `repost/<slot>/meta.json` (`status: published`, `permalink`, `media_id`, `published_at`) ו-CONTENT.md (עמודה חדשה לקישור החדש, או שורה "הועלה מחדש").
7. שולחים לבניה את רשימת הפוסטים הישנים להעברה לארכיון (העמודה האחרונה למטה).

כתובת המדיה: `https://raw.githubusercontent.com/automator2244-ai/google-reviews-project-video/claude/new-session-86yt7m/instagram/repost/<slot>/` (reel.mp4 או slide-NN.jpg).

## הפוסטים
| # | תיקייה | סוג | סדרה (פנימי) | מסך ראשון | הפוסט הישן (לארכיון) |
|---|---|---|---|---|---|
| 1 | 2026-10-27-0830 | קרוסלה | מהדלפק 1 | postit | https://www.instagram.com/p/De_N1PNEXK1/ |
| 2 | 2026-10-27-2130 | ריל | שאלה של מנהלת 1 | sms | https://www.instagram.com/reel/DfAm9aCDflo/ |
| 3 | 2026-10-28-0830 | ריל | מאחורי הקלעים 1 | chat | https://www.instagram.com/reel/DfBykEPjR7V/ |
| 4 | 2026-10-28-2130 | ריל | חשבון פשוט 1 | number | https://www.instagram.com/reel/DfDLy_1EbHC/ |
| 5 | 2026-10-29-0830 | קרוסלה | מהדלפק 2 | maps | https://www.instagram.com/p/DfEXZCHkSUB/ |
| 6 | 2026-10-29-2130 | ריל | שאלה של מנהלת 2 | face | https://www.instagram.com/reel/DfFwhpBjy8Q/ |
| 7 | 2026-10-30-0830 | קרוסלה | מהדלפק 3 | poster | https://www.instagram.com/p/DfG8HCQFSdQ/ |
| 8 | 2026-10-31-2200 | ריל | סיפור 1 | ink | https://www.instagram.com/reel/DfK9iNyDgvz/ |
| 9 | 2026-11-01-0830 | קרוסלה | מהדלפק 4 | newspaper | https://www.instagram.com/p/DfMFwY2DoV7/ |
| 10 | 2026-11-01-2130 | ריל | חשבון פשוט 2 | receipt | https://www.instagram.com/reel/DfNe_pMiuCR/ |
| 11 | 2026-11-02-0830 | ריל | מאחורי הקלעים 2 | notes | https://www.instagram.com/reel/DfOqkGRAbyX/ |
| 12 | 2026-11-02-2130 | ריל | שאלה של מנהלת 3 | green | https://www.instagram.com/reel/DfQDtgfCIWn/ |
| 13 | 2026-11-03-0830 | ריל | מספר אחד 1 | poster | https://www.instagram.com/reel/DfRPShVDH_w/ |
| 14 | 2026-11-03-2130 | ריל | דעה 1 | face | https://www.instagram.com/reel/DfSohfNgLum/ |
| 15 | 2026-11-04-0830 | קרוסלה | מהדלפק 5 | review | https://www.instagram.com/p/DfT0HSdkcvy/ |
| 16 | 2026-11-04-2130 | ריל | שאלה של מנהלת 4 | notif | https://www.instagram.com/reel/DfVNYPCClBp/ |
| 17 | 2026-11-05-0830 | ריל | מאחורי הקלעים 3 | poster | https://www.instagram.com/reel/DfWY6oGEesw/ |
| 18 | 2026-11-05-2130 | ריל | סיפור 2 | sms | https://www.instagram.com/reel/DfXyIPTDfe3/ |
| 19 | 2026-11-06-0830 | קרוסלה | צ׳קליסט שישי 1 | timer | https://www.instagram.com/p/DfY9uFaFe9A/ |
| 20 | 2026-11-07-2200 | ריל | הצעה 1 | green | https://www.instagram.com/reel/Dfc_K4rge9z/ |
| 21 | 2026-11-08-0830 | קרוסלה | מהדלפק 6 | review | https://www.instagram.com/p/DfeHSwDDjiH/ |
| 22 | 2026-11-08-2130 | ריל | שאלה של מנהלת 5 | poster | https://www.instagram.com/reel/Dffgl0dgEP5/ |
| 23 | 2026-11-09-0830 | קרוסלה | שתי גרסאות 1 | vs | https://www.instagram.com/p/DfgsGWxjkm3/ |
| 24 | 2026-11-09-2130 | ריל | דעה 2 | ink | https://www.instagram.com/reel/DfiFT-KiIBN/ |
| 25 | 2026-11-10-0830 | ריל | מאחורי הקלעים 4 | chat | https://www.instagram.com/reel/DfjQ2UmDCmZ/ |
| 26 | 2026-11-10-1300 | ריל | 10 שניות 1 | poster | https://www.instagram.com/reel/Dfjv_iFj7Cy/ |
| 27 | 2026-11-10-2130 | ריל | חשבון פשוט 3 | receipt | https://www.instagram.com/reel/DfkqD3lFQbS/ |
| 28 | 2026-11-11-0830 | קרוסלה | מהדלפק 7 | brand ink | https://www.instagram.com/p/Dfl1nhNlTdM/ |
| 29 | 2026-11-11-1300 | ריל | 10 שניות 2 | sms | לא עלה (הוחמץ) |
| 30 | 2026-11-11-2130 | ריל | צ'אט הצוות 1 | postit | https://www.instagram.com/reel/DfnO3C6ka3Y/ |
| 31 | 2026-11-12-0830 | ריל | מספר אחד 3 | vs | https://www.instagram.com/reel/DfoacQjDmCW/ |
| 32 | 2026-11-12-2130 | ריל | דעה 3 | search | לא עלה (הוחמץ) |
| 33 | 2026-11-13-0830 | קרוסלה | צ׳קליסט שישי 2 | notes | https://www.instagram.com/p/Dfq_Ou8FXCE/ |
