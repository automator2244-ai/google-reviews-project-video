import subprocess, sys, os
W = sys.argv[1]
src = W + "/tx/rec.mp4"; voice = W + "/voice.wav"
# sentence-boundary pauses (start, end) from silencedetect
pauses = [(1.2829,1.9534),(4.7310,5.3920),(10.9077,11.5308),(15.4431,15.8520),(20.2706,21.1274),(28.7905,29.2989),(31.1349,31.8973),
          (39.7946,40.2771),(43.8464,44.4232),(48.6334,49.1306),(52.3419,52.8841),(56.0829,57.0240),
          (61.0475,61.7203),(65.9338,66.5936),(69.6053,70.0439)]
start, end = 0.15, 75.08
segs = []; s = start
for (a, b) in pauses:
    segs.append((s, a + 0.12)); s = b - 0.10
segs.append((s, end))
# framing: A = full frame, B = closer on the face; alternate, finish on B for the call to action
SRC_W, SRC_H = 405, 720
def vf(z):
    base = f"scale={SRC_W}:{SRC_H}:flags=lanczos,setsar=1,hqdn3d=1.5:1.5:3:3,"
    if z == "B":
        base += "crop=352:626:49:87,"
    return base + "scale=1080:1920:flags=lanczos,unsharp=5:5:0.55:5:5:0,eq=contrast=1.04:saturation=1.07:brightness=0.01,fps=30,format=yuv420p"
lst = open(W + "/seg/list.txt", "w"); total = 0
for i, (a, b) in enumerate(segs):
    z = "A" if i % 2 == 0 else "B"
    a = round(a * 30) / 30; b = round(b * 30) / 30
    d = b - a; total += d
    out = f"{W}/seg/s{i:02d}.mov"
    fc = (f"[0:v]trim=start={a:.5f}:end={b:.5f},setpts=PTS-STARTPTS,{vf(z)}[v];"
          f"[1:a]atrim=start={a:.5f}:end={b:.5f},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st={d-0.02:.4f}:d=0.02[a]")
    subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-i",voice,"-filter_complex",fc,"-map","[v]","-map","[a]",
        "-c:v","libx264","-crf","12","-preset","fast","-c:a","pcm_s16le","-ar","48000",out], check=True)
    lst.write(f"file '{out}'\n"); print(i, z, f"{a:.2f}-{b:.2f}", f"{d:.2f}")
lst.close(); print("raw total", round(total,2), "at 1.3x", round(total/1.3,2))
