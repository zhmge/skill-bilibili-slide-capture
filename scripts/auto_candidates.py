#!/usr/bin/env python3
"""为每个 h2 列出时间区间内的所有候选 snap，供 AI 视觉选帧。

输入 links.json 格式（parse_links 产物）：
[
  {"block_id": "...", "title": "1.1 xxx 00:02:28", "bv": "...", "p": 43, "t": 148.6},
  ...
]

输出 candidates.json：每个 h2 的候选 snap 列表 + 自动建议帧。
AI 应该 Read 对应 contact_sheet，从候选里挑内容最完整的 1-N 帧。
"""
import argparse, json, os, re, sys


def is_h2(title: str) -> bool:
    """h2 标题带 N.M 数字编号，h3 通常没有。"""
    return bool(re.match(r'^\d+\.\d+\s', title))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("links", help="links.json 路径")
    ap.add_argument("--base", default="snaps", help="snap 根目录，默认 snaps")
    ap.add_argument("--buffer", type=int, default=15,
                    help="距下一个 h2 至少多少秒之前的 snap 才纳入自动建议，默认 15")
    ap.add_argument("--out", help="输出 candidates.json 路径，默认 stdout")
    args = ap.parse_args()

    links = json.load(open(args.links))
    h2 = [it for it in links if is_h2(it["title"])]

    result = []
    for i, it in enumerate(h2):
        p = it["p"]; t = it["t"]; bid = it["block_id"]; title = it["title"]
        # 下一个同 p 的 h2 时间戳
        next_t = None
        for j in range(i + 1, len(h2)):
            if h2[j]["p"] == p:
                next_t = h2[j]["t"]
                break
        if next_t is None:
            next_t = 1e9

        tl_path = os.path.join(args.base, f"p{p}", "timeline.json")
        if not os.path.exists(tl_path):
            print(f"WARN: 缺 timeline {tl_path}", file=sys.stderr)
            continue
        tl = json.load(open(tl_path))

        # 该区间内所有候选 snap
        cands = [s for s in tl if t - 1 <= s["time_sec"] < next_t]
        # 自动建议：距 next_t 至少 buffer 秒前的最后一帧
        sugg_pool = [s for s in cands if s["time_sec"] < next_t - args.buffer]
        suggested = sugg_pool[-1] if sugg_pool else (cands[-1] if cands else None)

        result.append({
            "block_id": bid,
            "p": p,
            "title": title,
            "t_start": t,
            "t_next": next_t if next_t < 1e9 else None,
            "candidates": [{"time": s["time_sec"], "file": s["file"]} for s in cands],
            "suggested": suggested["file"] if suggested else None,
        })

    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        open(args.out, "w").write(out)
        print(f"写入 {args.out}: {len(result)} 个 h2")
    else:
        print(out)


if __name__ == "__main__":
    main()
