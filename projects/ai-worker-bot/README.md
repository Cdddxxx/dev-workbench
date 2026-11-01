# AI 临时工 · AI Worker Bot

这是“AI 接真实任务、交真实成果，再把工作过程做成短视频”的**第一版可运行实验工程**，不是已上线的自主运营机器人。

**已实现（v0.1）**：读取明确任务 JSON → 生成可离线打开的 HTML 网页 → 记录 SHA-256 交付证据 → 生成 6 镜分镜、SRT 字幕、工作日志 → 可选离线渲染 **720×1280、28 秒、无配音**的 MP4。

**未实现**：接入大模型、通用任务规划、记忆、真人语音、自动读取评论、平台授权发布、收入核算。没有这些能力之前，不以“全自动运营”对外宣传。

## 最小运行

需要 Python 3.10+，不调用付费 API。以下命令在本项目目录执行：

```sh
# 命令行输出：网页交付、日志、分镜及字幕。无需安装依赖。
PYTHONPATH=src python -m ai_worker_bot examples/day-01.json --output output/day-001

# 本地可选视频渲染：需要免费 Pillow、FFmpeg 和中文字体。
python -m pip install -e '.[render]'
ai-worker examples/day-01.json --output output/day-001 --render

# 单元测试（无第三方测试库）
PYTHONPATH=src python -m unittest discover -s tests -v
```

运行后，打开 `output/day-001/deliverable/index.html` 查看真正的交付网页；查看 `WORKLOG.md` 和 `episode.json` 核查哪些结论有证据。`output/` 与 MP4 产物不提交 Git，避免隐私和大文件问题，源码与任务示例在仓库可重建。

## 系统边界与成本

- 第一版的“做网页”是**规则驱动的本地任务执行器**，不是 LLM Agent；任务输入只决定页面内容，不能执行任意 Shell 命令。
- 第一版 MP4 静音，字幕烧进画面，不能把它冒充成完整带配音成片。
- 当前代码的付费 API 调用为 0；**不等于所有真实成本均为 0**，人工、设备、托管和未来 API 成本均需另计。
- 发布和评论互动需要平台实际权限、授权和必要的内容审核；当前工程没有接入。
- 所有发布内容都应明确 AI 参与方式、真实能力与成果，不编造播放量、评论、收入或无人操作的记录。
- 该仓库是公开的；不提交密钥、真实账号材料、未授权评论数据或个人信息。尚未添加开源许可证。

## 接手入口

先看 [AGENTS.md](AGENTS.md)、[当前状态](docs/STATUS.md)、[项目决策](docs/DECISIONS.md)、[路线图](docs/ROADMAP.md)。项目事实、未完成事项和下一步统一维护在仓库，不以聊天窗口为权威记录。
