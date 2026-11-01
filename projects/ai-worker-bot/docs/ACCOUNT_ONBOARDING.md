# 工号001 · 离线入驻准备

## 当前暂停

用户否定先前昵称/简介；`profile_draft` 的 display_name / bio 现为 null，copy_status 为 rejected_pending_revision_do_not_submit。所有主页提交暂停，不把任何新候选固化为已批准默认文案。旧 output/onboarding-001 至003为历史离线成果，文案已过时，禁止执行。

## 已实现

运行 README 的命令，不需账号或第三方依赖。重用现有 `core.run_task`，不另造任务执行器。
产物：`profile-draft.json`、`character.json`、`preflight.json`、`audit.jsonl`、`NEXT.md`、
`task/deliverable/index.html` 与原有分镜/字幕/日志。重新读取 HTML 字节验证 SHA-256。
这是规则程序的真实文件产出，不是 LLM、真实浏览器验收、视频制作或发布。

主页文案继承 `persona.py` / `CHARACTER.md` 的001；头像候选位于 `assets/profile/avatar-001-v1.png`，生成来源与提示词见同目录 PROVENANCE.md；已看图，未用户审定、未平台裁切验收或上传。工作包 JSON 引用仓库相对路径，不假装已设置平台头像。
主体为用户（幕后老板），角色晋升不会扩大程序权限。

## 证据模型

默认所有身份和权限未知。可通过 `--account /private/path/account.json` 读入**私有清单**：
由 `empty_account(provider)` 返回精确字段；禁止额外字段，包括 cookie/token/password。
只使用不含个人信息的 opaque `account_ref` 和 `evidence_ref`（小写字母、数字、短横线）。
验证器限制格式，不可能判断某个合法字符串是否被误用来存密码；**切勿填真实凭据或 UID**。
输出工作包也需留在忽略目录，不把私人证据放入公开仓库。程序不读取证据引用目标。

状态严格区分：
- 身份：unverified / owner_attested / mismatch；
- 用户验证：unknown / required / operator_attested_complete；
- 权限：unknown / denied / revoked / operator_attested；
- 主页：draft / pending_submission / submitted_awaiting_readback / operator_attested_readback / mismatch；
- 安全：active / paused / access_denied。

`operator_attested*` 仅表示操作者声称完成，**不是程序已验证平台状态**。
主页回读须对应当前 `profile_digest()`（角色/文案版本的 SHA-256）和私有证据引用，
`observed_at` 须带时区、不在未来且24小时内。过期、账号错配、缺失、拒绝、撤销均阻塞。
操作者应在私有证据中核对平台、账号、版本；本模块不会认证这份声明。
提交待回读不等于主页已生效；手填状态不触发外部动作。

## 适配边界与安全退回

本期**没有平台适配器**，三个 provider 仅作目标标签。填写完整清单仍恒定返回
`connected=false` / `publish_enabled=false` / `reply_enabled=false`，并保留
`platform_adapter_not_implemented`、`avatar_asset_not_approved`。没有 mock 成功或后台重试。
遇到访问拒绝/人工验证/未知结果，只允许继续离线任务；不操作桌面、验证码、注册、授权或接受协议。

未来每个平台必须独立取得许可后实现：绑定正确身份的只读查询、权限查询、资料版本提交与回读，
撤销/过期检查、未知结果的先查后重试、隐私存储和审计；禁止直接信任本地 JSON 作为访问授权。
主页写入需另外明确授权；真实发布和回复还需各自适配器、逐次审批、原有
`operations.publication_blockers` 的内容质量/手机听审/素材与隐私/AI标识等审核。
本包直接输出原有全部默认发布阻塞项，不会以账号准备替代内容质量。

## 重复与失败

已有输出目录立即失败，不覆盖历史成果；输入不合法时不创建目录。
若生成中断留下部分目录，该目录不算成功工作包，请使用新目录重跑；不自动删数据。
测试包括三平台默认阻塞、完整声明仍不接入、提交不等于回读、资料摘要变化、
撤销/拒绝/暂停/身份错配、过期/未来证据、凭据字段拒绝、真实任务校验、重复调用与 CLI 平台错配。
