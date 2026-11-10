import test from "node:test";
import assert from "node:assert/strict";

import {
  buildDraft,
  canPublish,
  formSignature,
  formatVersion,
  identityFields,
  operatorErrorMessage,
  previewMatches,
  previewOutcome,
  statusReport,
} from "../../web/manage_logic.mjs";


const SOURCE = "web-manage-test";
const NOW = () => new Date("2026-11-07T10:00:00Z");
const ID = () => "draft-001";


function draft(values = {}, options = {}) {
  return buildDraft(values, SOURCE, {now: NOW, id: ID, ...options});
}


test("buildDraft normalizes form values into the event contract", () => {
  const event = draft({
    title: "  R4 WEB  ",
    progress: "42",
    currentStep: " 发布预览 ",
    status: " RUNNING ",
    description: " 管理页测试 ",
    tags: "a, b,, c ",
    contentSource: " Local Web ",
  });

  assert.equal(event.event_id, "web-draft-001");
  assert.equal(event.type, "panel.update");
  assert.equal(event.panel, "progress");
  assert.equal(event.source, SOURCE);
  assert.equal(event.occurred_at, "2026-11-07T10:00:00.000Z");
  assert.deepEqual(event.data, {
    title: "R4 WEB",
    progress: 42,
    current_step: "发布预览",
    status: "RUNNING",
    description: "管理页测试",
    tags: ["a", "b", "c"],
    source: "Local Web",
  });
});


test("buildDraft omits empty fields and clamps progress", () => {
  const empty = draft({});
  assert.deepEqual(empty.data, {});

  assert.equal(draft({progress: "140"}).data.progress, 100);
  assert.equal(draft({progress: "-5"}).data.progress, 0);
  assert.equal("progress" in draft({progress: "not-a-number"}).data, false);
  assert.deepEqual(draft({tags: "本地，复查"}).data.tags, ["本地", "复查"]);
});


test("statusReport rejects a Host without a publication source", () => {
  const report = statusReport({source: null, device: {}}, {event: draft(), frameVersion: "a"});
  assert.equal(report.label, "Host 未配置发布源");
  assert.equal(report.tone, "error");
});


test("statusReport waits before a draft is published", () => {
  const report = statusReport({source: SOURCE, device: {}}, null);
  assert.equal(report.label, "等待发布");
  assert.equal(report.tone, "idle");
});


test("statusReport waits for the Host to accept this draft", () => {
  const event = draft();
  const report = statusReport(
    {source: SOURCE, publish_id: "other", device: {}},
    {event, frameVersion: "a".repeat(64)},
  );
  assert.equal(report.label, "等待 Host 接受本次发布");
  assert.equal(report.tone, "warn");
});


test("statusReport flags a preview/published frame mismatch", () => {
  const event = draft();
  const report = statusReport(
    {
      source: SOURCE,
      publish_id: event.event_id,
      frame_version: "b".repeat(64),
      host_stage: "FRAME_READY",
      device: {},
    },
    {event, frameVersion: "a".repeat(64)},
  );
  assert.equal(report.label, "预览与发布帧不一致");
  assert.equal(report.tone, "error");
});


test("statusReport reports device completion as a software report", () => {
  const event = draft();
  const frameVersion = "a".repeat(64);
  const report = statusReport(
    {
      source: SOURCE,
      publish_id: event.event_id,
      frame_version: frameVersion,
      host_stage: "FRAME_READY",
      device: {
        accepted_frame_version: frameVersion,
        refresh_stage: "DEVICE_REFRESH_FLOW_COMPLETE",
      },
    },
    {event, frameVersion},
  );
  assert.equal(report.label, "刷新流程完成（软件报告）");
  assert.equal(report.tone, "ok");
});


test("statusReport distinguishes accepted and frame-ready states", () => {
  const event = draft();
  const frameVersion = "a".repeat(64);
  const accepted = statusReport(
    {
      source: SOURCE,
      publish_id: event.event_id,
      frame_version: frameVersion,
      host_stage: "FRAME_READY",
      device: {accepted_frame_version: frameVersion},
    },
    {event, frameVersion},
  );
  assert.equal(accepted.label, "设备已接受");
  assert.equal(accepted.tone, "ok");

  const ready = statusReport(
    {
      source: SOURCE,
      publish_id: event.event_id,
      frame_version: frameVersion,
      host_stage: "FRAME_READY",
      device: {},
    },
    {event, frameVersion},
  );
  assert.equal(ready.label, "帧已就绪，等待设备取帧");
  assert.equal(ready.tone, "ok");

  const hostAccepted = statusReport(
    {
      source: SOURCE,
      publish_id: event.event_id,
      host_stage: "HOST_ACCEPTED",
      device: {},
    },
    {event, frameVersion},
  );
  assert.equal(hostAccepted.label, "Host 已接收，等待设备取帧");
  assert.equal(hostAccepted.tone, "ok");
});


test("statusReport warns while a device has not accepted this frame", () => {
  const event = draft();
  const report = statusReport(
    {
      source: SOURCE,
      publish_id: event.event_id,
      host_stage: "HOST_ACCEPTED",
      device: {last_seen: "2026-11-07T10:00:01Z"},
    },
    {event, frameVersion: "a".repeat(64)},
  );
  assert.equal(report.label, "设备已通信，等待本次帧接受");
  assert.equal(report.tone, "warn");
});


test("statusReport defaults to waiting for a device report", () => {
  const event = draft();
  const report = statusReport(
    {source: SOURCE, publish_id: event.event_id, device: {}},
    {event, frameVersion: "a".repeat(64)},
  );
  assert.equal(report.label, "等待设备报告");
  assert.equal(report.tone, "warn");
});


test("statusReport reports UNKNOWN when the status poll fails", () => {
  const event = draft();
  const report = statusReport(
    {
      source: SOURCE,
      publish_id: event.event_id,
      frame_version: "a".repeat(64),
      device: {
        accepted_frame_version: "a".repeat(64),
        refresh_stage: "DEVICE_REFRESH_FLOW_COMPLETE",
      },
    },
    {event, frameVersion: "a".repeat(64)},
    {pollFailed: true, lastSuccessText: "10:00:01"},
  );
  assert.equal(report.tone, "error");
  assert.match(report.label, /状态未知/);
  assert.match(report.label, /10:00:01/);

  const withoutSuccess = statusReport(null, null, {pollFailed: true});
  assert.equal(withoutSuccess.label, "状态未知（读取失败）");
});


test("previewOutcome ignores a previous publication's frame version", () => {
  const event = draft();
  const outcome = previewOutcome(
    {
      source: SOURCE,
      publish_id: "web-earlier",
      frame_version: "b".repeat(64),
      host_stage: "FRAME_READY",
      device: {},
    },
    {event, frameVersion: "a".repeat(64)},
  );
  assert.equal(outcome.tone, "idle");
  assert.equal(outcome.label, "预览已生成；发布后将与 Host 帧版本比对。");
});


test("previewOutcome compares only the preview's own publication", () => {
  const event = draft();
  const frameVersion = "a".repeat(64);
  const preview = {event, frameVersion};

  const match = previewOutcome(
    {publish_id: event.event_id, frame_version: frameVersion},
    preview,
  );
  assert.equal(match.tone, "ok");
  assert.match(match.label, /一致/);

  const mismatch = previewOutcome(
    {publish_id: event.event_id, frame_version: "b".repeat(64)},
    preview,
  );
  assert.equal(mismatch.tone, "error");
  assert.equal(mismatch.label, "预览与发布帧不一致");

  const pending = previewOutcome({publish_id: event.event_id}, preview);
  assert.equal(pending.tone, "warn");
  assert.match(pending.label, /帧尚未就绪/);

  assert.equal(previewOutcome(null, null).tone, "idle");
});


test("formSignature tracks effective form content only", () => {
  assert.equal(formSignature({title: " A "}), formSignature({title: "A"}));
  assert.equal(formSignature({tags: "a, b"}), formSignature({tags: "a,b"}));
  assert.notEqual(formSignature({title: "A"}), formSignature({title: "B"}));
  assert.notEqual(formSignature({progress: "10"}), formSignature({progress: "11"}));
});


test("operatorErrorMessage localizes renderer failures without echoing input", () => {
  assert.match(operatorErrorMessage("Layout: tags exceed column"), /标签/);
  assert.match(operatorErrorMessage("Layout: text exceeds column: '秘密'"), /安全排版/);
  assert.match(operatorErrorMessage("Layout: text crosses graphic boundary: 'x'"), /安全排版/);
  assert.match(operatorErrorMessage("Font: missing glyph U+1F600"), /字体/);
  assert.match(operatorErrorMessage("Text has no visible contrast"), /对比/);
  assert.match(operatorErrorMessage("Panel data is incomplete or invalid"), /不完整/);
  assert.match(operatorErrorMessage("Business frame unavailable"), /业务帧/);
  assert.equal(operatorErrorMessage([{msg: "field required"}]), "请求格式不正确：请检查表单内容。");
  assert.equal(operatorErrorMessage("internal detail", "HTTP 500"), "HTTP 500");
  assert.equal(operatorErrorMessage(undefined, "HTTP 503"), "HTTP 503");
});


test("previewMatches requires the same publication and frame version", () => {
  const event = draft();
  const frameVersion = "a".repeat(64);
  assert.equal(
    previewMatches(
      {publish_id: event.event_id, frame_version: frameVersion},
      {event, frameVersion},
    ),
    true,
  );
  assert.equal(
    previewMatches(
      {publish_id: event.event_id, frame_version: "b".repeat(64)},
      {event, frameVersion},
    ),
    false,
  );
  assert.equal(previewMatches({publish_id: event.event_id}, {event, frameVersion}), false);
});


test("canPublish requires a current preview and a Host source", () => {
  const event = draft();
  const preview = {event, frameVersion: "a".repeat(64)};
  assert.equal(canPublish(preview, false, SOURCE), true);
  assert.equal(canPublish(preview, true, SOURCE), false);
  assert.equal(canPublish(preview, false, null), false);
  assert.equal(canPublish(null, false, SOURCE), false);
  assert.equal(canPublish({event, frameVersion: ""}, false, SOURCE), false);
  assert.equal(canPublish({...preview, published: true}, false, SOURCE), false);
});


test("formatVersion shortens opaque frame versions", () => {
  const version = "a".repeat(64);
  assert.equal(formatVersion(version), "aaaaaaaaaaaa…");
  assert.equal(formatVersion(`"${version}"`), "aaaaaaaaaaaa…");
  assert.equal(formatVersion(""), "—");
  assert.equal(formatVersion("abc"), "abc");
});


test("identityFields reads the selected page status for the connection card", () => {
  const fields = identityFields({
    source: "takeout",
    frame_format: "epd-t-400x300-mono1-msb-v1",
    device: {
      firmware_version: "round2-r3d-ota1",
      last_seen: "2026-11-10T12:10:24Z",
    },
  });

  assert.equal(fields.source, "takeout");
  assert.equal(fields.frameFormat, "epd-t-400x300-mono1-msb-v1");
  assert.equal(fields.firmware, "round2-r3d-ota1");
  assert.equal(fields.lastSeen, "2026-11-10T12:10:24Z");
});

test("identityFields keeps the idle wording when the device never reported", () => {
  const fields = identityFields({source: "memo"});

  assert.equal(fields.source, "memo");
  assert.equal(fields.frameFormat, "--");
  assert.equal(fields.firmware, "--");
  assert.equal(fields.lastSeen, "未通信");
});

test("identityFields degrades to UNKNOWN when the status poll failed", () => {
  const fields = identityFields(null, {failed: true});

  assert.equal(fields.source, "UNKNOWN");
  assert.equal(fields.frameFormat, "UNKNOWN");
  assert.equal(fields.firmware, "UNKNOWN");
  assert.equal(fields.lastSeen, "UNKNOWN");
});
