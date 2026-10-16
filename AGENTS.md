# 维护本仓库

- 默认使用简体中文沟通和编写说明。
- 本仓库是 `project-dev` 与 `project-handoff` 的源码，不是工具箱业务项目。工具箱仅为使用指南中的示例。
- 接手先读 [README.md](README.md)、[维护背景](docs/MAINTENANCE.md) 和 [当前进展](docs/STATUS.md)，再按任务读取相关 Skill。无需过去的聊天记录。
- 修改 Skill 时按可用的 `skill-creator` 规范处理，以本仓库的 `skills/` 为开发源；验证和交付后再按用户要求更新本机安装副本，保留本地定制。另一台电脑的安装副本需单独更新。
- 修改时保持按需读取和提示词简洁。普通改动不重跑需求对齐，不为每个小任务新开工作者。
- 维护本套装沿用现有 `main` 分支与远端；业务新项目的 `main` / `dev/work` 约定不应反过来强加到本仓库。
- 文档改动检查链接、示例与源码是否一致；Skill 改动验证格式、引用和实际受影响流程。改变 Git 隔离或交接逻辑时，用 Git 和 Python 3 运行 `tests/verify_project_dev_flow.py`，它仅在临时本地仓库中演练。
- `docs/STATUS.md` 保留当前快照；设计与重要决定变化时更新 `docs/MAINTENANCE.md`，不复制整段聊天。

<!-- project-handoff:start -->
## 本仓库的交接

- 开工时核对本地修改、远端和分支，安全获取更新后重新读取 `.project-handoff.json` 指向的资料。存在分叉或冲突时先保留并报告。
- 收工时更新进展，审查并提交本次相关文件，按用户授权推送，再核对远端实际提交号。推送失败时明确报告未同步。
- 密钥和凭据不进入仓库；新电脑依赖仓库资料和实际验证接手。
<!-- project-handoff:end -->
