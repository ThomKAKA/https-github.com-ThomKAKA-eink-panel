"""Development-only dynamic JSON service for testing HTTPJSONAdapter."""

from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI


app = FastAPI(title="E-Ink Mock HTTP API", version="0.1.0")
_counts = {"progress": 0, "stats": 0, "flow": 0}
_progress_sequence = (
    {
        "progress": 72,
        "status": "开发中",
        "current_step": "准备代码改动",
        "description": "Codex 正在分析项目",
    },
    {
        "progress": 73,
        "status": "开发中",
        "current_step": "建立动态数据",
        "description": "Codex 正在接入刷新序列",
    },
    {
        "progress": 81,
        "status": "开发中",
        "current_step": "验证面板刷新",
        "description": "Codex 正在运行自动测试",
    },
    {
        "progress": 81,
        "status": "等待确认",
        "current_step": "等待人工确认",
        "description": "请确认当前改动后继续",
    },
    {
        "progress": 100,
        "status": "已完成",
        "current_step": "任务完成",
        "description": "Codex 开发任务已完成",
    },
)
_stats_primary_values = ("258.42M", "260.11M", "264.73M")
_flow_stage_names = ("准备", "执行", "完成")


def _now() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")


@app.get("/progress")
def progress() -> dict:
    _counts["progress"] += 1
    step_index = min(_counts["progress"] - 1, len(_progress_sequence) - 1)
    step = _progress_sequence[step_index]
    return {
        "title": "CODEX",
        "progress": step["progress"],
        "current_step": step["current_step"],
        "status": step["status"],
        "description": step["description"],
        "tags": ["CODEX", "LIVE"],
        "updated_at": _now(),
        "source": "Codex Progress Mock",
    }


@app.get("/stats")
def stats() -> dict:
    _counts["stats"] += 1
    value_index = min(_counts["stats"] - 1, len(_stats_primary_values) - 1)
    return {
        "title": "TODAY TOKEN",
        "primary_value": _stats_primary_values[value_index],
        "primary_label": "TODAY TOKEN",
        "secondary_value": "8.51B",
        "secondary_label": "TOTAL TOKEN",
        "cost": "$406.92",
        "breakdown": [
            {"name": "GPT-5.x", "value": 66.7, "unit": "%"},
            {"name": "Claude", "value": 32.7, "unit": "%"},
            {"name": "Other", "value": 0.6, "unit": "%"},
        ],
        "updated_at": _now(),
        "source": "Mock HTTP API",
    }


@app.get("/flow")
def flow() -> dict:
    _counts["flow"] += 1
    phase_index = min(_counts["flow"] - 1, len(_flow_stage_names) - 1)
    stages = []
    for index, name in enumerate(_flow_stage_names):
        if phase_index == len(_flow_stage_names) - 1:
            status = "done"
        else:
            status = "done" if index < phase_index else "active" if index == phase_index else "pending"
        stages.append({"name": name, "status": status})
    phase_name = _flow_stage_names[phase_index]
    return {
        "title": phase_name,
        "category": "TASK FLOW",
        "eta": str(phase_index + 1),
        "eta_unit": "阶段",
        "distance": f"{phase_index + 1}/3",
        "description": f"当前状态：{phase_name}",
        "current_stage": phase_index,
        "stages": stages,
        "updated_at": _now(),
        "source": "Mock HTTP API",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("examples.http_server:app", host="127.0.0.1", port=9000, reload=False)
