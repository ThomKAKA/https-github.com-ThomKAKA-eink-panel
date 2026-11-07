# Git Baseline Plan

当前目录已经是 Git 仓库，`main` 分支尚无提交，因此不要再次执行 `git init`。

## 为什么现在建立基线

Phase 3 Stable 已形成可运行、可测试的数据与刷新底座。首次提交可以提供明确的回退点，后续
真实数据或硬件工作出现问题时，能够区分 Phase 3 基线与新阶段改动。

## 建议步骤

1. 完成 STEP-006，由用户核对灾后重建的已完成清单和范围限制。
2. 检查 `git status`，确认 `.env`、密钥、Token、运行缓存和个人数据没有进入暂存范围。
3. 暂存经过确认的项目文件并检查 staged diff。
4. 创建首次提交，建议提交信息：`Phase 3 stable baseline`。
5. 在确认测试和浏览器验收记录无误后创建 annotated tag：`v0.3.0-phase3-stable`。

本计划只记录建议，不在 STEP-005 中执行提交、打标签、reset 或 clean。
