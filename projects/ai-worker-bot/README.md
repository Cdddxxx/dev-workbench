# AI 临时工 · AI Worker Bot

这是“AI 接真实任务、交真实成果，再把执行过程做成短视频”的**本地实验工程**，不是已上线的自主运营机器人。

**当前 v0.2（M1 第一条动态样片）**：读取规范任务 JSON → 生成可离线打开的静态 HTML 落地页 → 记录 SHA-256 → 生成 7 幕分镜、SRT、日志 → 程序化生成 **720×1280、15fps** 的动态 MP4；如安装免费 `espeak`，可加上离线机器中文配音。已在本地渲染出 **43 秒、H.264 + AAC** 的样片。

**仍未实现**：接入大模型、处理一般复杂任务、自主决策与记忆、自然的高品质中文人声、真实浏览器/手机端验收、自动读评论、平台授权发布或收入核算。

## 快速运行

要求 Python 3.10+；生成网页不需要第三方依赖。需要渲染视频时安装 Pillow（免费）、FFmpeg 和支持中文的字体；机器配音还需要本地 `espeak`（免费）。**整个流程不使用付费 API。**

在本目录运行：

```sh
# 1. 只生成真实 HTML 成品 + 7 幕分镜 + SRT + 工作日志
PYTHONPATH=src python -m ai_worker_bot examples/day-01.json --output output/day-001

# 2. 生成无声动态视频
python -m pip install -e '.[render]'
ai-worker examples/day-01.json --output output/day-001 --render

# 3. 生成带离线机器配音的动态视频（安装 espeak 后）
ai-worker examples/day-01.json --output output/day-001 --render --voice

# 4. 测试
PYTHONPATH=src python -m unittest discover -s tests -v
```

运行后打开 `output/day-001/deliverable/index.html` 查看交付的 HTML；播放 `episode.mp4` 预览样片；查看 `WORKLOG.md`、`episode.json` 对照真实执行方式、时长、视频元数据与已验证范围。`output/` 不提交 Git，避免大文件和敏感任务信息；代码可重现产物。

## 边界与审计

- v0.2 仍是**规则驱动的静态网页生成器**，不会自主编程，也没有任何付费 LLM。输入的任务描述不能授权它执行任意 Shell 命令，更不能视为所有自然语言任务都已完成。
- 视频里页面图是**根据网页源码绘制的界面示意**，明确标注“非浏览器实录”；不能当成浏览器测试或网站部署的证据。
- 视频里中文配音来自免费的本地 eSpeak，发音质量有限，**正式发布前要人工听审**。如果没有安装配音工具，`--voice` 会报错，不会冒充有声音。
- **发布操作、评论互动、运营成本、API 权限**均未接入。样片未经手机端、真人观看效果和平台发布审核验收。
- 本程序付费 API 调用为 0；不等于人工、设备、托管等总成本均为 0。
- 当前是公开仓库，不提交密钥、私人评论、Cookie、个人账号数据、未获授权媒体；没有开源许可证。

## 接手与追踪

从 [AGENTS.md](AGENTS.md)、[STATUS](docs/STATUS.md)、[ROADMAP](docs/ROADMAP.md)、[DECISIONS](docs/DECISIONS.md) 了解真实进度。优先解决创作质量和真实设备验收，再考虑大模型 Agent 或平台自动化。仓库是进度的权威来源，聊天不是。

## GitHub 持续集成与视频交付

仓库根目录 `.github/workflows/ai-worker-demo.yml` 在每次相关源代码提交时，用 GitHub 的**公开仓库标准 Linux Runner** 执行测试、重建视频和校验视频/HTML 的 SHA-256；然后上传可直接下载的视频和网页打包产物为 GitHub Actions Artifact（保留 14 天）。这保证之后可以在不依赖聊天临时文件的情况下重建样片。Actions 在仓库配置允许的情况下才会执行，务必检查实际运行结果。

公开仓库标准 Runner 当前不按计算分钟计费，但 GitHub 账户的 Artifact 存储仍受额度限制；本项目的测试包约 1 MB。
