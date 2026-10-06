# 踩坑与经验

## 下载

- **yt-dlp 在当前环境常被 HTTP 412 拦截**（即使加 UA/Referer/cookie 也不行）。直接走 `dl_bilibili_hd.py` 调 web API 更稳。
- **未登录最高 480P（qn=32）**。要 1080P 必须传 SESSDATA cookie：
  - 让用户从浏览器开发者工具 Application → Cookies → `SESSDATA` 拷贝
  - 写到环境变量 `BILIBILI_SESSDATA`，不要硬编码进脚本
  - 用户通常会要求任务结束后销毁；任务最后 `unset BILIBILI_SESSDATA` 并删除任何含 cookie 的临时文件
- **durl 可能截断**：B 站直链偶尔只下到前半段文件（文件有几十 MB 但时长只有期望的一半），导致后半段抽帧返回空。脚本已加 ffprobe 校验，发现时长 < 期望 90% 就警告，必须删除重下。
- 部分分 P 本身最高 720P，不要强求 1080。

## 抽帧与稳定画面

- 用 **ffmpeg 1fps + imagehash.pHash 相邻帧汉明距离**，阈值 8。
  - 阈值太小（4）会把同页渐进动画拆成多张相近快照，contact sheet 刷屏
  - 阈值太大（15+）会把不同页合并，丢失内容
- 视频是 PPT 式渐进出现（文字/代码逐行 add），一页内容会产生**多个稳定中间态**：
  - 选帧时取"本页 PPT 内容最完整、覆盖最多 h3"的那一帧
  - 一页讲不完的内容，允许**同一 h2 配多张**
- 全屏整帧不要裁切；鼠标指针偶尔遮挡不影响理解。

## 选帧（核心教训）

- **不要机械取"区间最后一张"**：最后一张经常是下一个 h2 的标题空白页，或者切题但内容没填满的帧。
- **必须 AI 视觉判断**：用 `auto_candidates.py` 列出区间内所有候选，Read contact sheet 缩略图墙，逐帧看：
  - 标题、正文、图表、绿色气泡注释是否都加载完
  - 这帧是不是已经切到下一个 h2 的主题了
  - 内容是否覆盖了该 h2 下所有 h3
- **h2 过滤**：只配标题匹配 `^\d+\.\d+\s` 的 h2；h3（无数字编号）不配，否则会和 h2 重复。

## Contact Sheet

- 用 ImageMagick `montage` + `convert` 给每帧加黄色顶条时间戳（mm:ss）。
- 一屏缩略图墙，agent 一次性 Read 看完，脑内定位每个 h2 对应的"内容最完整"帧。
- 文件名 `snap_NNN_t<秒>s.jpg` 直接对应时间。

## 飞书文档插入

- `lark-cli docs +media-insert` 只能插到**文末**，上传后必须 `block_move_after` 挪到目标 h2 后。
- 多张图连续插：先插第 1 张到 h2 后拿 new_id，再把第 2 张 `move_after` 到 new_id，依次链式。
- `--doc` 用 doc_id（docx token），不要用 `/wiki/...` URL。
- 删除旧图用 `scripts/delete_imgs.py`：fetch 全文 → 正则找 `<img id=...>` → 逐个 block_delete。
- 不要加 `--caption`（用户明确不要图注）。

## 与用户对齐的关键原则

- 只给 h2 配图，h3 不配
- h2 的图要完整覆盖该 h2 下所有 h3 内容，不够就多张
- 不裁切、不加图注、要高清
- SESSDATA 用后即焚，任务结束销毁
