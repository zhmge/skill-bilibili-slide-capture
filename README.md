# bilibili-slide-capture

从 PPT 式讲课录屏中提取**完整幻灯片**帧，按笔记里的章节时间戳挑选内容最完整的一页，插入飞书文档对应标题下。

## 解决的问题

讲课录屏里的幻灯片是渐进式出现的——文字、图表、代码逐行加载。按时间戳直接截一帧，大概率截到的是内容还没填满的中间态，或者已经切到下一页的空白标题页。这个 skill 的做法是：先按画面相似度把视频切成「稳定画面」，再让 agent 逐个章节做视觉判断，从候选帧里挑出内容最完整的那一张。

## 处理流程

```
B 站视频 ──下载──▶ mp4 ──1fps 抽帧 + pHash 聚类──▶ 稳定帧
                                                     │
飞书笔记 ──提取 h2 标题与时间戳──▶ links.json ──按区间列出候选──▶
                                                     │
                              agent 视觉选帧 ──▶ choices.json
                                                     │
                                        插入飞书文档 h2 标题下
```

## 功能

- **高清下载**：直连 B 站 web API 取 durl 直链，绕开 `yt-dlp` 在当前环境下被 HTTP 412 拦截的问题；支持按分 P 范围批量下载，下载后用 `ffprobe` 校验时长，识别 durl 截断。
- **稳定帧提取**：`ffmpeg` 1fps 抽帧，`imagehash` pHash 相邻帧汉明距离 ≥8 判为新画面，避免渐进式动画刷出大量近似快照。
- **候选生成与选帧**：按 h2 时间区间列出全部候选帧，并给出参考建议帧；配合 ImageMagick 生成的缩略图墙（每帧带时间戳标注）做视觉判断。
- **飞书文档回填**：图片先插入文末，再通过 `block_move_after` 挪到目标 h2 之后；同一 h2 配多张图时链式插入。附旧图清理脚本。

## 依赖

- `ffmpeg`、`ffprobe`
- ImageMagick（`montage`、`convert`）
- Python 包：`imagehash`、`Pillow`
- `lark-cli` 并已登录（飞书文档读写）

## 开始使用

整个目录放入 agent skills 目录即可，`SKILL.md` 是入口，其中给出了完整的分步命令。

取用 1080P 需要 B 站登录态：从浏览器开发者工具 Application → Cookies 复制 `SESSDATA`，通过环境变量 `BILIBILI_SESSDATA` 传入。未登录时最高 480P。

## 产物

最终产物是飞书文档里插好的幻灯片图片，不产出额外文件。中间产物（`videos/`、`snaps/`、`links.json`、`candidates.json`、`choices.json`）属于工作区数据，已在 `.gitignore` 中排除。

## 已知限制

- 只适用于 PPT 式录屏。连续剧情视频、真人出镜无 PPT 的画面不适用。
- 只给 h2 标题配图，h3 不配；h2 的图需完整覆盖其下所有 h3 内容，不够时配多张。
- 抽帧会在画面里保留鼠标指针；全屏整帧不裁切，指针遮挡不影响理解。
- `delete_imgs.py` 会删除文档内**全部**图片 block。文档里若原本有手工放置的图片，需先确认。

## License

[MIT](LICENSE)
