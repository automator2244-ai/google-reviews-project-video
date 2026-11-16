// One dashboard per audience. A recipient belongs to the segment in recipients.segment (NULL = the first one).
export interface Segment {
  key: string; // "" = dental clinics, served at /admin. Others are served at /admin/<key>.
  label: string;
  sheet: string; // the leads sheet of this audience (private to the owner's Google account)
  template: string; // default WhatsApp message in the dashboard
}

export const SEGMENTS: Segment[] = [
  {
    key: "",
    label: "רופאי שיניים",
    sheet: "https://docs.google.com/spreadsheets/d/13bRjc6ezK3SAYv4YQFW8SEUj3FYZdTM-Frg3Hlb_xS8/edit",
    template: "היי {שם}, הכנתי לך סרטון קצר במיוחד בשבילך: {קישור}",
  },
  {
    key: "vet",
    label: "וטרינרים",
    sheet: "https://docs.google.com/spreadsheets/d/1hNJ2djD2Uqqy5U2k2KTEKquzg0Oik9uSI41PecaImkA/edit",
    template: "היי {שם}, הכנתי לך סרטון קצר במיוחד בשבילך: {קישור}",
  },
];
