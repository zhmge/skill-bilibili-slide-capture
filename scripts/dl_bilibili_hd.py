#!/usr/bin/env python3
"""下载B站分P视频到本地（最高可用清晰度）。

用法:
  python3 dl_bilibili_hd.py <bv_id> [--p START_P END_P] [--cookie SESSDATA] [--out DIR]

- 未登录最高 480P；提供 SESSDATA cookie 后可拿 1080P。
- 直接调 B 站 web API（/x/web-interface/view + /x/player/playurl），绕开
  yt-dlp 在当前环境被 412 拦截的问题。
- cookie 只在本次进程内使用，不要落盘。
"""
import argparse, json, os, subprocess, sys, urllib.request, urllib.parse


def http_get(url, cookie=None, referer=None):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    if cookie:
        req.add_header("Cookie", cookie)
    if referer:
        req.add_header("Referer", referer)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def pick_play_url(playinfo, prefer_qn=80):
    """从 playurl 返回里挑 durl 直链，优先 qn=80(1080)，降级到 64/32。"""
    accept_quality = playinfo.get("data", {}).get("accept_quality", [])
    chosen = None
    for qn in [prefer_qn, 64, 32, 16]:
        if qn in accept_quality:
            chosen = qn
            break
    if chosen is None:
        chosen = accept_quality[0]
    # 取当前 durl 模式（未开 dash 的话）
    url = playinfo["data"]["durl"][0]["url"]
    return url, chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bv_id")
    ap.add_argument("--p", type=int, nargs=2, default=[1, None],
                    help="分P范围，起始和结束（1-based，包含）")
    ap.add_argument("--cookie", default=os.environ.get("BILIBILI_SESSDATA", ""),
                    help="SESSDATA cookie 字符串；可省略走环境变量 BILIBILI_SESSDATA")
    ap.add_argument("--out", default="videos")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    view = http_get(f"https://api.bilibili.com/x/web-interface/view?bvid={args.bv_id}",
                    cookie=args.cookie)
    aid = view["data"]["aid"]
    pages = view["data"]["pages"]
    start, end = args.p[0], (args.p[1] or len(pages))
    print(f"aid={aid} 共{len(pages)}P，下载 p{start}~p{end}")

    for p in pages:
        pid = p["page"]
        if not (start <= pid <= end):
            continue
        out = os.path.join(args.out, f"p{pid}.mp4")
        if os.path.exists(out) and os.path.getsize(out) > 1024 * 1024:
            print(f"[p{pid}] 已存在，跳过")
            continue
        play = http_get(
            f"https://api.bilibili.com/x/player/playurl?bvid={args.bv_id}&cid={p['cid']}&qn=80&platform=html5&high_quality=1",
            cookie=args.cookie,
            referer=f"https://www.bilibili.com/video/{args.bv_id}?p={pid}",
        )
        if "durl" not in play.get("data", {}):
            print(f"[p{pid}] 无法获取 durl: {play}")
            continue
        url, qn = pick_play_url(play)
        print(f"[p{pid}] qn={qn} 标题={p['part'][:30]}")
        subprocess.run([
            "curl", "-L", "-o", out,
            "-H", "User-Agent: Mozilla/5.0",
            "-H", f"Referer: https://www.bilibili.com/video/{args.bv_id}",
            *(["-H", f"Cookie: {args.cookie}"] if args.cookie else []),
            url,
        ], check=False)

        # 下载后校验时长，防止 durl 截断导致后半段缺失
        expected_dur = p.get("duration", 0)
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", out],
            capture_output=True, text=True,
        )
        try:
            actual = float(r.stdout.strip())
        except ValueError:
            actual = 0
        if expected_dur and actual < expected_dur * 0.9:
            print(f"[p{pid}] ⚠️ 时长异常: 期望 {expected_dur}s, 实际 {actual:.0f}s，建议删除重下！")
        else:
            print(f"[p{pid}] 完成, 时长 {actual:.0f}s")


if __name__ == "__main__":
    main()
