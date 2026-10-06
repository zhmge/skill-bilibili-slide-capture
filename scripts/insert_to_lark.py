#!/usr/bin/env python3
"""把选好的截图批量插入飞书文档，定位到指定 block（通常是 h2 标题）之后。

choices.json 格式（list）:
  [
    ["<anchor_block_id>", "<分p目录>", ["snap_001_t0123s.jpg", ...], "标题备注"],
    ...
  ]

用法:
  python3 insert_to_lark.py <doc_id> choices.json
"""
import argparse, json, subprocess, sys


def media_insert(doc, path):
    r = subprocess.run(
        ["lark-cli", "docs", "+media-insert", "--doc", doc,
         "--file", path, "--align", "center"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(r.stdout)["data"]["block_id"]


def move_after(doc, anchor, src):
    subprocess.run(
        ["lark-cli", "docs", "+update", "--doc", doc,
         "--command", "block_move_after",
         "--block-id", anchor, "--src-block-ids", src],
        capture_output=True, text=True, check=True,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc")
    ap.add_argument("choices", help="choices.json 路径")
    ap.add_argument("--base", default="snaps", help="snaps 根目录")
    args = ap.parse_args()

    choices = json.load(open(args.choices))
    ok = fail = 0
    for i, item in enumerate(choices, 1):
        anchor, pdir, files, title = item
        print(f"[{i}/{len(choices)}] {title}")
        cur = anchor
        for f in files:
            path = f"{args.base}/{pdir}/{f}"
            try:
                new_id = media_insert(args.doc, path)
                move_after(args.doc, cur, new_id)
                cur = new_id  # 多张图时后续接在前一张后面
                ok += 1
            except Exception as e:
                fail += 1
                print(f"  FAIL {path}: {e}", file=sys.stderr)
    print(f"完成: 成功{ok} 失败{fail}")


if __name__ == "__main__":
    main()
