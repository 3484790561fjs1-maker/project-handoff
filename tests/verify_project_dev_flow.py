"""在临时本地仓库中验证隔离、WIP 推送、另一份克隆接手和安全快进。"""

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile


def git(cwd, *args, check=True):
    env = os.environ.copy()
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_TERMINAL_PROMPT="0",
    )
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    if check and result.returncode:
        raise RuntimeError(f"git {args[0]} failed: {result.stderr}")
    return result


def write(root, relative, value):
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")


def identity(repo):
    for key, value in {
        "user.name": "Project Dev Verification",
        "user.email": "verification@example.invalid",
        "commit.gpgsign": "false",
        "core.autocrlf": "false",
    }.items():
        git(repo, "config", "--local", key, value)


def commit(repo, message, paths):
    git(repo, "add", "--", *paths)
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def push_and_verify(repo, branch):
    git(repo, "push", "-u", "origin", f"HEAD:refs/heads/{branch}")
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    remote = git(repo, "ls-remote", "--heads", "origin", f"refs/heads/{branch}")
    assert remote.stdout.split()[0] == head
    return head


def exercise(root):
    checks = []
    remote, home, office = (root / name for name in ("remote.git", "home", "office"))
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "--bare", "--initial-branch=main", str(remote))
    home.mkdir()
    git(home, "init", "--initial-branch=main")
    identity(home)
    git(home, "remote", "add", "origin", str(remote))
    write(home, ".project-handoff.json", json.dumps({
        "version": 1,
        "remote": "origin",
        "repository_url": str(remote),
        "branch": "dev/work",
        "documents": {"status": "docs/STATUS.md"},
    }))
    write(home, "README.md", "# 临时工具箱验证\n")
    write(home, "docs/STATUS.md", "公共基准已保存；下一步开发独立工具。\n")
    write(home, "src/tools/.gitkeep", "")
    base = commit(home, "initial shared base", [
        ".project-handoff.json", "README.md", "docs/STATUS.md", "src/tools/.gitkeep",
    ])
    push_and_verify(home, "main")
    git(home, "switch", "-c", "dev/work")

    json_worker, time_worker = root / "json-worker", root / "time-worker"
    git(home, "worktree", "add", "-b", "feat/json-tool", str(json_worker), base)
    git(home, "worktree", "add", "-b", "feat/time-tool", str(time_worker), base)
    write(json_worker, "src/tools/json_tool.py",
          "import json\ndef format_json(raw):\n"
          "    return json.dumps(json.loads(raw), ensure_ascii=False, indent=2)\n")
    write(json_worker, "docs/tasks/json-tool.md", "JSON 格式化已实现并针对输入验证。\n")
    write(time_worker, "src/tools/time_tool.py",
          "from datetime import datetime\ndef unix_seconds(raw):\n"
          "    return int(datetime.fromisoformat(raw).timestamp())\n")
    write(time_worker, "docs/tasks/time-tool.md", "WIP：时间转换已实现，界面尚未完成。\n")
    assert not (home / "src/tools/json_tool.py").exists()
    assert not (json_worker / "src/tools/time_tool.py").exists()
    assert not (time_worker / "src/tools/json_tool.py").exists()
    checks.append("两个功能目录文件隔离，未提交内容没有泄漏到主控或其他任务。")

    formatter = runpy.run_path(str(json_worker / "src/tools/json_tool.py"))["format_json"]
    assert json.loads(formatter('{"answer":42}')) == {"answer": 42}
    converter = runpy.run_path(str(time_worker / "src/tools/time_tool.py"))["unix_seconds"]
    assert converter("1970-01-01T00:00:00+00:00") == 0
    commit(json_worker, "implement json tool", ["src/tools/json_tool.py", "docs/tasks/json-tool.md"])
    commit(time_worker, "wip time tool before UI", ["src/tools/time_tool.py", "docs/tasks/time-tool.md"])
    json_sha = push_and_verify(json_worker, "feat/json-tool")
    time_sha = push_and_verify(time_worker, "feat/time-tool")
    checks.append("两个功能分支分别提交、推送，并以远端实际 SHA 核验。")

    git(home, "merge", "--no-ff", "feat/json-tool", "-m", "integrate verified json tool")
    assert (home / "src/tools/json_tool.py").exists()
    assert not (home / "src/tools/time_tool.py").exists()
    write(home, "docs/TASKS.md", (
        "# 当前任务\n\n"
        f"- JSON：已集成到阶段分支，来源 feat/json-tool，远端提交 {json_sha}\n"
        f"- 时间工具：WIP，分支 feat/time-tool，远端提交 {time_sha}，"
        "进展文件 docs/tasks/time-tool.md；下一步完成界面。\n"
    ))
    write(home, "docs/STATUS.md", "JSON 已集成；时间工具 WIP；稳定 main 尚未合并本阶段。\n")
    commit(home, "save stage handoff", ["docs/TASKS.md", "docs/STATUS.md"])
    stage_sha = push_and_verify(home, "dev/work")
    assert git(home, "rev-parse", "main").stdout.strip() == base
    checks.append("已验证模块可集成；未完成功能保留独立分支；稳定 main 未被强行更新。")

    git(root, "clone", str(remote), str(office))
    identity(office)
    config = json.loads((office / ".project-handoff.json").read_text(encoding="utf-8"))
    git(office, "switch", "-c", config["branch"], "--track", f"origin/{config['branch']}")
    assert git(office, "rev-parse", "HEAD").stdout.strip() == stage_sha
    assert "feat/time-tool" in (office / "docs/TASKS.md").read_text(encoding="utf-8")
    office_worker = root / "office-time-worker"
    git(office, "worktree", "add", "-b", "feat/time-tool", str(office_worker), "origin/feat/time-tool")
    assert git(office_worker, "rev-parse", "HEAD").stdout.strip() == time_sha
    assert "WIP" in (office_worker / "docs/tasks/time-tool.md").read_text(encoding="utf-8")
    assert (office_worker / "src/tools/time_tool.py").exists()
    assert (office_worker / ".project-handoff.json").read_text(encoding="utf-8") == (
        office / ".project-handoff.json"
    ).read_text(encoding="utf-8")
    checks.append("第二份独立克隆能先读取主控交接，再从远端恢复 WIP 功能与任务说明；共享配置未改写。")

    occupied = git(office, "worktree", "add", str(root / "duplicate-worker"), "feat/time-tool", check=False)
    assert occupied.returncode != 0
    assert git(office_worker, "rev-parse", "HEAD").stdout.strip() == time_sha
    checks.append("同一分支已被 Worktree 占用时拒绝重复检出，原任务成果保留。")

    write(office_worker, "docs/tasks/time-tool.md", "WIP：公司继续，下一步完善界面错误提示。\n")
    commit(office_worker, "wip office checkpoint", ["docs/tasks/time-tool.md"])
    office_sha = push_and_verify(office_worker, "feat/time-tool")
    git(home, "fetch", "origin")
    assert not git(time_worker, "status", "--porcelain").stdout.strip()
    git(time_worker, "merge", "--ff-only", "origin/feat/time-tool")
    assert git(time_worker, "rev-parse", "HEAD").stdout.strip() == office_sha
    assert "公司继续" in (time_worker / "docs/tasks/time-tool.md").read_text(encoding="utf-8")
    checks.append("公司副本保存后，家里对应任务可以安全快进接续。")

    write(home, "docs/STATUS.md", "开始下一阶段；主控交接目标继续使用 dev/work。\n")
    write(home, "docs/TASKS.md", f"时间工具仍为 WIP，最新核验提交 {office_sha}。\n")
    commit(home, "record next stage on persistent branch", ["docs/STATUS.md", "docs/TASKS.md"])
    next_stage_sha = push_and_verify(home, "dev/work")
    another_office = root / "next-office-visit"
    git(root, "clone", str(remote), str(another_office))
    entry = json.loads((another_office / ".project-handoff.json").read_text(encoding="utf-8"))
    git(another_office, "switch", "-c", entry["branch"], "--track", f"origin/{entry['branch']}")
    assert git(another_office, "rev-parse", "HEAD").stdout.strip() == next_stage_sha
    assert "下一阶段" in (another_office / "docs/STATUS.md").read_text(encoding="utf-8")
    assert git(home, "rev-parse", "main").stdout.strip() == base
    checks.append("跨阶段继续复用固定主控分支；首次克隆旧 main 仍可根据入口定位最新进展。")
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    sandbox = tempfile.TemporaryDirectory(prefix="project-dev-check-", dir=report.parent)
    sandbox_root = Path(sandbox.name).resolve()
    try:
        assert sandbox_root.is_relative_to(report.parent)
        checks = exercise(sandbox_root)
    finally:
        # 只允许清理刚刚创建且位于报告输出目录内的临时环境。
        if sandbox_root.is_relative_to(report.parent) and sandbox_root.name.startswith("project-dev-check-"):
            sandbox.cleanup()
    stamp = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    text = "# project-dev Git 流程演练\n\n"
    text += f"时间：{stamp}\n\n结果：{len(checks)} 项检查通过。\n\n"
    text += "\n".join(f"- {check}" for check in checks)
    text += (
        "\n\n演练使用本机临时 bare 仓库和两份独立克隆，未访问真实业务仓库或修改 Git 全局配置。"
        "临时环境已清理。\n\n"
        "这验证了 Skill 采用的 Git 隔离与接续路径；不代表已经完成真实 AI 并行行为评估、"
        "GitHub 登录/推送测试、Superpowers 集成测试或实际两台电脑的运行验证。\n"
    )
    report.write_text(text, encoding="utf-8")
    print(f"PASS: {len(checks)} workflow checks. Report: {report}")


if __name__ == "__main__":
    main()
