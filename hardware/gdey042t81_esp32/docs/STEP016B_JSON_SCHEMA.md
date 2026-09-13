# STEP016B — Local JSON Schema

状态：INTERFACE FROZEN / IMPLEMENTATION NOT RUN / TESTS NOT RUN。
基线：`dbd7b8c2956513f74e623cb6321e0d59c4eb16a7`；承接 [STEP016A](STEP016A_ARCHITECTURE_FREEZE.md)。

## 兼容边界

本规范是用户确认的离线输入边界细化：project/step/timestamp 仅为未来离线文件字段，映射到现有 ProgressPanelData，不重命名模型字段或改变公开 API。
它不是当前 LocalJSONAdapter 已支持的协议。现有 [Adapter](../../../adapters/base.py) 会补 source/updated_at；现有模型也有默认值和类型处理。未来离线入口必须先严格校验原始输入，再映射，不能把已补时间的数据当成用户提供的快照。
现有普通数据源、Stats/Flow 和 STEP016A 历史文档不修改。

## 输入规则

输入为 UTF-8 JSON，顶层必须是对象。只允许下表字段；拒绝未知字段、重复键、别名混用、null、错误类型及非法日期时间。不加入网络、HTTP、远程同步或配置凭据字段。
project/step/status/description 和每个 tag 去除首尾空白；必填文本及 tag 处理后不得为空。timestamp 必须原样符合固定格式，不用系统时间补齐。

| 字段 | 类型 | 必填/默认 | 映射到 ProgressPanelData |
| --- | --- | --- | --- |
| project | string | 必填，非空 | title |
| step | string | 必填，非空 | current_step |
| progress | integer | 必填，0..100，拒绝 bool、浮点数、数字字符串 | progress |
| status | string | 必填，非空，自由状态文字 | status |
| timestamp | string | 必填，YYYY-MM-DD HH:mm，有效公历日期/时间，Asia/Shanghai | updated_at |
| description | string | 可选，默认空字符串 | description |
| tags | string[] | 可选，默认空数组，最多两个非空标签 | tags |

映射后固定 `source="Local JSON"`，输入不得自行指定 source/title/current_step/updated_at。时间为本地快照时间，不接受时区后缀、秒或替代格式，不自动转换为当前时间。
字符串宽度由 [布局与字体验收](STEP016B_PAGE_LAYOUT.md) 决定，不用字符数保证不溢出。status 不是联网健康状态；既有 WAITING DATA/UPDATE FAILED 显示分支保持可识别，不将无效输入自动转成这些可发布页面。

## 有效示例

```json
{
  "project": "EINK PANEL",
  "step": "接口冻结",
  "progress": 60,
  "status": "进行中",
  "timestamp": "2026-09-13 14:30",
  "description": "离线页面验证",
  "tags": ["LOCAL", "V1"]
}
```

此示例仅说明格式，60 不代表项目真实完成比例；示例仍需未来字体/布局测试。

## 拒绝示例与结果

| 输入变化 | 结果 |
| --- | --- |
| progress=true、60.0、"60"、-1 或 101 | 类型或范围错误 |
| timestamp 缺失、空值、2026-02-30 10:00 | 必填或日历错误，不补时间 |
| step="   " 或 tags=[""] | 空文本错误 |
| 同时包含 project 和 title | 未知/混用字段错误，无优先级回退 |
| tags 有三个元素，或不是数组 | 结构错误 |
| {"project":"A","project":"B"} | 重复键错误，即使普通解析器会覆盖也必须拒绝 |
| 顶层数组、畸形 JSON | 格式错误 |

失败必须阻止 [Render 发布](STEP016B_RENDER_INTERFACE.md)，不覆盖旧有效产物，不生成固件或触发上传。规则测试见 [测试计划](STEP016B_TEST_PLAN.md)，本轮未执行。
