# 简历桥 JobBridge v0.1.0

本地优先的求职资料、申请记录与安全填表技术预览。不是全平台海投服务，不保证录用，不宣称已适配真实招聘系统。工作名称尚未核准商标。

## 恢复、运行

仓库使用 8 个 Base64 分片保存完整、可复原的源码快照，避免会话中断丢失。恢复脚本验证 SHA256 后仅解压普通文件，不联网、不执行源代码、不覆盖已修改文件。解压后均为正常可编辑源文件。

```bash
git clone --branch jobbridge-v0 https://github.com/Cdddxxx/dev-workbench.git
cd dev-workbench
python3 projects/jobbridge/restore.py
cd projects/jobbridge/app
python3 scripts/build.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory dist
# 在浏览器打开 http://127.0.0.1:8765
```

需要 Python 3.10+；构建不需要 npm 包或密钥。`dist/jobbridge-portable.html` 是单文件版；推荐固定的本地 HTTP 地址，避免 file:// 存储的浏览器差异。`dist/jobbridge-extension.zip` 为开发者模式安装包，不是应用商店已上架扩展。

## 已实现

- 多版本职业档案；TXT/Markdown/DOCX 本地提取、预览、本人确认；教育及工作经历可编辑。
- 求职看板、原始链接、去重、手动状态、CSV 与日历 ICS 导出。
- 五个官方渠道入口；不是职位数据库，也不是已验证兼容清单。
- 常规网页字段识别预览、确认填写、撤销；敏感字段与歧义字段跳过、已有值不覆盖。
- AES-GCM 加密备份、恢复与删除。浏览器日常存储并非加密保险箱。
- Chrome MV3 扩展仅请求 activeTab / scripting / storage；不索取招聘账号。

当前不支持 PDF 自动解析、云端 AI 生成、全网职位聚合、原生 App、小程序、自动提交或聊天。BOSS 相关域名默认停用。其他站点也必须遵守授权和平台规则。

## 验证证据

2026-11-06：18/18 Node 单元测试和 40/40 自建离线 DOM/UI 检查通过。离线检查模拟 Storage，不等于真实浏览器端到端验收；本地受管理浏览器阻止 URL 导航与扩展安装，未绕过策略。`tests/real_browser_e2e.py` 为独立真实浏览器验证脚本，实际运行状态以 CI 日志为准。没有真实 ATS 兼容率或节时率数据。

```bash
node --test tests/core.test.cjs
# 可用的独立测试环境：
python3 -m pip install playwright==1.57.0
python3 -m playwright install --with-deps chromium
python3 tests/real_browser_e2e.py
```

先启动上述 HTTP 服务再执行浏览器测试。仅使用脚本内虚构数据。

## 运营状态与恢复入口

`docs/STATUS.md` 记录授权、上线与证据。恢复后查看 `app/docs/PRD.md`、`app/docs/TEST_RESULTS.md`、`app/ops/OPERATIONS.md`。本版本无付费入口、无遥测服务器、无真实用户或收入验证。Render 工作区尚待用户明确确认，未创建公网服务；不使用 Vercel Hobby 承载商业项目。

反馈不得提交真实简历、手机号、身份证、登录凭据或带访问令牌的 URL。仅提供版本、浏览器、非敏感复现步骤及脱敏字段标签。严禁把公开 Issue 当成简历收集表。

源码档案 SHA256：`94c21ca4aa21718e15d905bdf7e703773647dcbe4e972a1216104b4e2a57e4fa`。八个远端分片的 Git blob 哈希已与本地原文件逐一比对一致，恢复后的 18 项单元测试已再次通过。
