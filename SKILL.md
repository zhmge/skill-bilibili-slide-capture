---
name: bilibili-slide-capture
description: 从 PPT 式讲课录屏（B站网课、考研课、培训回放）中提取"完整幻灯片"帧，按笔记里的章节时间戳选最完整的一页，无图注插入飞书文档对应标题下。适用：(1) 用户给了一份带 B 站视频时间戳链接的学习笔记，要求"去视频里截完整 PPT 图插回笔记"；(2) 视频是渐进式 PPT（文字/图表逐行出现），需要识别每个知识点对应的完整页面而非当前帧；(3) 批量处理多个分 P、几十到上百个 h2 章节。不要用于：连续剧情视频、真人出镜无 PPT、只要某一帧截图的简单任务。
---

# PPT 录屏截图回填笔记

把 PPT 式录屏里的完整幻灯片，批量截出来插回飞书笔记。

## 前置依赖

- `ffmpeg`、`ffprobe`、`montage`（ImageMagick）
- Python 包：`imagehash`、`Pillow`
- `lark-cli` 已登录（飞书文档读写）

## 工作流

### 1. 读笔记，列出 h2 与时间戳

让用户给飞书文档链接（或 doc_id）和 B 站 BV 号。

用 `lark-cli docs +fetch --detail with-ids` 读文档，提取每个 h2 标题的 block_id 和对应视频 p/时间戳，存成 `links.json`。

**只处理 h2**：h2 标题带数字编号（如 `6.2 首次适应算法`）；h3（无编号或子知识点）不配图——h2 的图会覆盖其下所有 h3。如果 links 里混了 h3，过滤掉标题不匹配 `^\d+\.\d+\s` 的条目。

### 2. 下载视频

```bash
export BILIBILI_SESSDATA="用户提供的cookie"  # 要 1080P 才需要
python3 scripts/dl_bilibili_hd.py <BV号> --p <起> <止> --out videos
```

- 没 cookie 最高 480P；要 1080P 让用户从浏览器开发者工具 Application→Cookies→`SESSDATA` 拷贝
- cookie 走环境变量，不落盘；任务结束 unset 并删除任何含 cookie 的文件
- **下载后脚本会自动用 ffprobe 校验时长**，如果实际时长 < 期望 90%，说明 durl 截断了，删掉重下

### 3. 抽帧，pHash 聚类稳定画面

```bash
for p in <起>..<止>; do
  python3 scripts/extract_slides.py videos/p${p}.mp4 --out snaps/p${p} --threshold 8
done
```

- 1fps 抽帧；相邻 pHash 汉明距离 ≥8 视为新画面
- 输出 `snaps/pXX/snap_NNN_t<秒>s.jpg` + `timeline.json`
- 阈值 8 适合 PPT 渐进式出现；阈值太小会刷屏，太大合并不同页

### 4. 列候选，AI 视觉选帧

```bash
python3 scripts/auto_candidates.py links.json --base snaps --out candidates.json
```

脚本会列出每个 h2 区间 `[t, 下一个 h2 时间戳]` 内的所有 snap，并自动建议"距下一个 h2 至少 15 秒前的最后一帧"。

然后：
1. 对每个 p 跑 `bash scripts/make_contact_sheet.sh snaps/pXX 5` 生成缩略图墙
2. Read `contact_pXX.jpg`，**逐个 h2 视觉判断**：
   - 选内容最完整的帧（标题、正文、图表、绿色气泡注释都加载出来）
   - 排除明显是下一个 h2 标题空白页的帧
   - 一个 h2 讲了多页 PPT 就选多张（覆盖全部 h3）
   - 脚本的 suggested 只是参考，必须看画面确认
3. 落成 `choices.json`：
```json
[
  ["<h2_block_id>", "p28", ["snap_014_t0291s.jpg"], "1.1 xxx"],
  ["<h2_block_id>", "p28", ["snap_022_t0414s.jpg", "snap_031_t0572s.jpg"], "1.2 yyy"]
]
```

### 5. 清空旧图（如有），插入新图

```bash
# 如果之前插过图，先清空
python3 scripts/delete_imgs.py <doc_id>

# 插入新图
python3 scripts/insert_to_lark.py <doc_id> choices.json --base snaps
```

- 不加 `--caption`（无图注）
- 多张图链式接在 h2 后
- `--doc` 用 doc_id（docx token），不要用 `/wiki/...` URL

## 关键原则

- **只给 h2 配图，h3 不配**
- h2 的图要**完整覆盖该 h2 下所有 h3 内容**，不够就多张
- 全屏整帧不裁切、不加图注、要高清
- cookie 用后即焚，任务结束 unset 并删除含 cookie 的文件

## 通用化说明

选帧逻辑（pHash 抽稳定帧 + AI 视觉判断）不绑定 B 站。如果换其他平台的 PPT 录屏：
- 替换 `dl_bilibili_hd.py` 为对应平台的下载脚本即可
- 抽帧、候选生成、contact sheet、飞书插入流程不变
- 只要输入是"本地 mp4 + h2 时间戳列表"就能跑

## 踩坑经验

见 [references/lessons.md](references/lessons.md)。
