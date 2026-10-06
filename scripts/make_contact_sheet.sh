#!/usr/bin/env bash
# 给一个 snaps/pXX/ 目录生成带时间戳标注的缩略图墙 contact.jpg。
# 用法: make_contact_sheet.sh <snaps_dir> [--tile 5]
set -e
DIR="$1"
TILE="${2:-5}"
OUT="${DIR}/../contact_$(basename $DIR).jpg"
TMP=$(mktemp -d)

for f in "$DIR"/snap_*.jpg; do
  bn=$(basename "$f")
  t=$(echo "$bn" | grep -oP 't\K[0-9]+')
  mm=$((10#$t/60)); ss=$((10#$t%60))
  convert "$f" -resize 360x \
    -gravity north -background yellow -splice 0x20 \
    -pointsize 11 -fill black -annotate +3+3 "t=${mm}:${ss}" \
    "$TMP/$bn"
done

montage "$TMP"/snap_*.jpg -tile "${TILE}x" -geometry +2+2 -background gray "$OUT"
rm -rf "$TMP"
echo "已生成: $OUT"
