#!/usr/bin/env python3
"""删除飞书文档里所有图片 block（用于重选图前清空旧图）。

用法：
  python3 delete_imgs.py <doc_id>

注意：会删文档里全部 <img> block。如果文档原本有用户自己放的图，先确认。
"""
import json, re, subprocess, sys


def main():
    if len(sys.argv) < 2:
        print("用法: python3 delete_imgs.py <doc_id>", file=sys.stderr)
        sys.exit(1)
    doc_id = sys.argv[1]

    r = subprocess.run(
        ["lark-cli", "docs", "+fetch", "--doc", doc_id, "--detail", "with-ids", "--doc-format", "xml"],
        capture_output=True, text=True,
    )
    data = json.loads(r.stdout)
    content = data["data"]["document"]["content"]

    img_ids = re.findall(r'<img[^>]*\bid="([^"]+)"', content)
    print(f"找到 {len(img_ids)} 张图")

    deleted = 0
    for bid in img_ids:
        rr = subprocess.run(
            ["lark-cli", "docs", "+update", "--doc", doc_id,
             "--command", "block_delete", "--block-id", bid],
            capture_output=True, text=True,
        )
        if rr.returncode == 0:
            deleted += 1
        else:
            print(f"删 {bid} 失败: {rr.stderr[:200]}", file=sys.stderr)
    print(f"已删 {deleted} 张")


if __name__ == "__main__":
    main()
