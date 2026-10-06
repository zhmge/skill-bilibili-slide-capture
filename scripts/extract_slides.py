#!/usr/bin/env python3
"""从视频里提取"稳定幻灯片"快照。

思路（已在B站PPT式讲课录屏上验证）：
  1. ffmpeg 1fps 均匀抽帧
  2. 用 imagehash 的 pHash 算相邻帧汉明距离
  3. 距离 < 阈值（默认 8）视为"未变"，丢弃；距离 >= 阈值视为"新一页/新状态"，保留
  4. 输出保留帧为 snap_NNN_t<秒>s.jpg，并写 timeline.json

阈值参考：8 适合 PPT 渐进式出现文字/代码；12 更激进（合并相近动画）。
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

try:
    import imagehash
    from PIL import Image
except ImportError:
    print("需要 pip install imagehash Pillow", file=sys.stderr)
    sys.exit(1)


def extract_fps(video, out_dir, fps=1):
    os.makedirs(out_dir, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(video),
        "-vf", f"fps={fps}",
        "-q:v", "3",
        str(out_dir / "frame_%05d.jpg"),
    ], check=True, capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True, help="快照输出目录 snaps/pXX/")
    ap.add_argument("--threshold", type=int, default=8,
                    help="相邻帧 pHash 汉明距离阈值，>= 视为新画面")
    ap.add_argument("--fps", type=int, default=1)
    args = ap.parse_args()

    raw_dir = Path(args.out) / "_raw"
    extract_fps(args.video, raw_dir, args.fps)

    files = sorted(raw_dir.glob("frame_*.jpg"))
    print(f"共抽 {len(files)} 帧，阈值={args.threshold}")

    kept = []
    last_hash = None
    for i, f in enumerate(files):
        h = imagehash.phash(Image.open(f))
        if last_hash is None or (h - last_hash) >= args.threshold:
            kept.append((i, h, f))
            last_hash = h

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    timeline = []
    for idx, (i, h, f) in enumerate(kept, 1):
        sec = i / args.fps
        new_name = out / f"snap_{idx:03d}_t{int(round(sec)):04d}s.jpg"
        os.replace(f, new_name)
        timeline.append({"idx": idx, "time_sec": sec,
                         "file": new_name.name, "phash": str(h)})
    # 清理多余帧
    for f in files:
        if f.exists():
            f.unlink()
    raw_dir.rmdir()

    with open(out / "timeline.json", "w") as fp:
        json.dump(timeline, fp, ensure_ascii=False, indent=2)
    print(f"保留 {len(timeline)} 个稳定快照 -> {out}")


if __name__ == "__main__":
    main()
