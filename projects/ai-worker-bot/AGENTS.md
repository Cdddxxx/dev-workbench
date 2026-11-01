# 接手说明 / AI Worker Bot

本目录是 AI 临时工的唯一代码与项目事实入口。

1. 先读 `README.md`、`docs/STATUS.md`、`docs/CHARACTER.md`、`docs/LEVEL_SYSTEM.md`、`docs/DECISIONS.md` 和 `docs/ROADMAP.md`，然后再修改工程。
2. 不要把“本地规则程序”称为“已接入 LLM 的自主 Agent”；不能把渲染完成称为发布完成。
4. 迭代必须包含可运行源码、可重现的演示任务、实际测试和状态更新。把真正完成的功能列入 STATUS 的 Verified，失败/待验证的功能如实记录。
4. 不允许把密钥、凭据、账号 Cookie、私人评论、未授权素材放进公开仓库；遵守平台 API 授权及人工审核界限。
5. 默认不产生付费调用或部署费用；如必须付费，应先列用途、上限、退出方式并由用户明确同意。
6. 避免引入多平台运营、社交自动回评或复杂商业化框架；先证明可重复交付有实际价值的视频样片。
7. 所有任务执行有审计记录，不隐瞒人为参与。必要时通过 Issues 追踪，不使用聊天作为唯一待办清单。

验证指令：`PYTHONPATH=src python -m unittest discover -s tests -v`。视频需要 Pillow、FFmpeg 和中文字体；如缺环境，明确区分测试通过与视频渲染通过。

v0.3 迭代注意：`render.py` 输出 7 幕动态竖屏视频；`voice.py` 只用离线 eSpeak 制作机器人配音。不要把“基于源码的网页示意图”当成浏览器实录；剧情OS不等于真实隐秘行为；任何视频发布前需在手机上听审。完整复现命令：

```sh
PYTHONPATH=src python -m ai_worker_bot examples/day-01.json --output output/day-001 --render --voice
PYTHONPATH=src python -m unittest discover -s tests -v
```

## 接手新规则：声音、发布和评论

- 必须先读 docs/AGENT_ARCHITECTURE.md 和 docs/VOICE_SELECTION.md。完整能力不等于当前已实现，禁止虚报自动发片或自主回评。
- eSpeak 仅限工程演示，禁止作为发布级中文主声线；新的 Qwen3-TTS / Dylan 仍待实际试听。没有模型就明确报错，不要偷偷回退。
- 发布必须先通过真结果、真人手机听审、素材授权与隐私、AI/虚构演绎标识和用户明确审核。API 发布还需官方权限及当次用户明确感知。评论先保留可追溯来源、生成未发送草稿。
- 新代码 src/ai_worker_bot/operations.py 是离线闸门，不执行任何平台动作。运行完整单测验收。
