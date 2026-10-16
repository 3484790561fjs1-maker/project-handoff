# 项目开发与交接套装

用一个入口 `$project-dev`，完成需求对齐、设计、开发、验证，以及公司和家里两台电脑间的交接。

**默认直接开发；适合拆分时最多两路并行，由 AI 判断。** 不需要按项目大小切换流程。

👉 **[简明实操指南：直接复制提示词使用](docs/project-dev-使用说明.md)**

换电脑继续改进这套 Skill 时，先读 [维护背景](docs/MAINTENANCE.md) 与 [当前进展](docs/STATUS.md)，再按指南最后一步操作；不需要原聊天记录。

## 包含什么

| Skill | 作用 | 版本 |
| --- | --- | --- |
| `project-dev` | 统一开发入口，按需安排并行任务，汇总开发和交接 | 1.0.0 |
| `project-handoff` | 维护规则、架构和进展，执行开工与收工同步 | 1.0.0 |

Superpowers 为可选组件，需另外安装；未安装时使用内置的基础需求与计划流程。UI 沿用你提供的专属规则。

## 安装

在另一台电脑的 Codex 中发送：

```text
从我的私有仓库 3484790561fjs1-maker/project-handoff 的 main 分支，
安装 skills/project-dev 和 skills/project-handoff。
缺少的使用 skill-installer 安装；已存在的先检查差异，备份并保留本地定制后再更新。
请使用本机已有的 GitHub 登录凭据。
```

需要有该私有仓库的访问权限。安装后技能未出现时重启 Codex。安装方式参考 [OpenAI 官方技能说明](https://developers.openai.com/codex/skills/)。

## 日常用法

```text
使用 $project-dev，开工同步。同步成功且环境就绪后，接着上次的下一项任务开发。
```

```text
使用 $project-dev，收工同步，明天换电脑继续。保存相关分支，更新交接资料，提交推送并核验远端。
```

详细场景见上方实操指南。只需要原有交接功能时，仍可单独调用 `$project-handoff`。

本套装在你发出指令后执行，不是后台同步服务。业务项目另建仓库；聊天记录、运行中的任务、密钥和本地数据库不会随 Git 同步。
