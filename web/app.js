const preview = document.querySelector("#panel-preview");
const panelTitle = document.querySelector("#panel-title");
const panelButtons = [...document.querySelectorAll("[data-panel]")];
const sampleControl = document.querySelector(".sample-control");
const sampleSelect = document.querySelector("#sample-select");
const sourceSelect = document.querySelector("#source-select");
const sourceKind = document.querySelector("#source-kind");
const sourceState = document.querySelector("#source-state");
const sourceLastSuccess = document.querySelector("#source-last-success");
const sourceNextRefresh = document.querySelector("#source-next-refresh");
const intervalSelect = document.querySelector("#interval-select");
const autoOffButton = document.querySelector("#auto-off");
const autoOnButton = document.querySelector("#auto-on");
const normalButton = document.querySelector("#normal-mode");
const einkButton = document.querySelector("#eink-mode");
const refreshButton = document.querySelector("#refresh");
const pngButton = document.querySelector("#export-png");
const bmpButton = document.querySelector("#export-bmp");
const renderStatus = document.querySelector("#render-status");

let samples = [];
let dataSources = [];
let currentData = null;
let mode = "normal";
let panelType = "progress";
let currentPreviewUrl = null;
let autoRefreshEnabled = false;
let autoRefreshTimer = null;
let refreshGeneration = 0;
let activeRefresh = null;

function selectedSampleData() {
  return samples.find((sample) => sample.id === sampleSelect.value)?.data ?? {};
}

function selectedSource() {
  return dataSources.find((source) => source.id === sourceSelect.value) ?? null;
}

function renderData() {
  return currentData ?? selectedSampleData();
}

async function requestRender(format = "png") {
  const response = await fetch(
    `/api/panels/${panelType}/render?mode=${mode}&format=${format}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(renderData()),
    },
  );
  if (!response.ok) {
    throw new Error(`Render failed: ${response.status}`);
  }
  return response.blob();
}

async function renderPreview() {
  const blob = await requestRender("png");
  const nextUrl = URL.createObjectURL(blob);
  preview.src = nextUrl;
  preview.classList.toggle("eink", mode === "eink");
  if (currentPreviewUrl) {
    URL.revokeObjectURL(currentPreviewUrl);
  }
  currentPreviewUrl = nextUrl;
}

function setMode(nextMode) {
  mode = nextMode;
  normalButton.classList.toggle("active", mode === "normal");
  einkButton.classList.toggle("active", mode === "eink");
  renderStatus.textContent = "RENDERING";
  renderPreview()
    .then(() => {
      renderStatus.textContent = `READY / ${mode.toUpperCase()}`;
    })
    .catch((error) => {
      renderStatus.textContent = "RENDER FAILED";
      console.error(error);
    });
}

async function loadSamples(targetPanel = panelType) {
  const response = await fetch(`/api/samples/${targetPanel}`);
  if (!response.ok) {
    throw new Error(`Samples failed: ${response.status}`);
  }
  const nextSamples = await response.json();
  if (targetPanel !== panelType) {
    return false;
  }
  samples = nextSamples;
  sampleSelect.replaceChildren();
  for (const sample of samples) {
    const option = document.createElement("option");
    option.value = sample.id;
    option.textContent = sample.label;
    sampleSelect.append(option);
  }
  sampleSelect.value = samples.some((sample) => sample.id === "default")
    ? "default"
    : (samples[0]?.id ?? "");
  return true;
}

async function loadDataSources(targetPanel = panelType) {
  const response = await fetch(`/api/data-sources/${targetPanel}`);
  if (!response.ok) {
    throw new Error(`Data sources failed: ${response.status}`);
  }
  const nextDataSources = await response.json();
  if (targetPanel !== panelType) {
    return false;
  }
  dataSources = nextDataSources;
  sourceSelect.replaceChildren();
  for (const source of dataSources) {
    const option = document.createElement("option");
    option.value = source.id;
    option.textContent = source.label;
    sourceSelect.append(option);
  }
  const defaultSource = dataSources.find((source) => source.default) ?? dataSources[0];
  sourceSelect.value = defaultSource?.id ?? "";
  updateSourceControls();
  return true;
}

function compactTime(value) {
  if (!value) {
    return "--";
  }
  const text = String(value);
  return text.length >= 16 ? text.slice(11, 16) : text;
}

function updateSourceControls() {
  const source = selectedSource();
  sampleControl.hidden = source?.type !== "mock";
  sourceKind.textContent = source?.label ?? "--";
  sourceState.textContent = source?.status && source.status !== "IDLE" ? source.status : "IDLE";
  sourceLastSuccess.textContent = compactTime(source?.last_success);
  sourceNextRefresh.textContent = "--";
}

function updateSourceStatus(outcome) {
  const source = selectedSource();
  sourceKind.textContent = source?.label ?? outcome.source ?? "--";
  sourceState.textContent = outcome.status ?? "ERROR";
  sourceLastSuccess.textContent = compactTime(outcome.last_success);
  sourceNextRefresh.textContent = compactTime(outcome.next_refresh);
}

async function refreshFromSource(generation = refreshGeneration) {
  const source = selectedSource();
  if (!source) {
    throw new Error("No compatible data source");
  }
  const requestPanel = panelType;
  const requestSourceId = source.id;

  renderStatus.textContent = "FETCHING DATA";
  const response = await fetch(`/api/data-sources/${source.id}/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sample_id: source.type === "mock" ? sampleSelect.value : null,
      interval_seconds: autoRefreshEnabled ? Number(intervalSelect.value) : 0,
    }),
  });
  if (!response.ok) {
    throw new Error(`Data refresh failed: ${response.status}`);
  }

  const outcome = await response.json();
  if (
    generation !== refreshGeneration ||
    requestPanel !== panelType ||
    requestSourceId !== sourceSelect.value
  ) {
    return outcome;
  }
  currentData = outcome.data ?? {};
  updateSourceStatus(outcome);
  await renderPreview();
  if (outcome.stale) {
    renderStatus.textContent = "READY / STALE DATA";
  } else if (!outcome.success) {
    renderStatus.textContent = "DATA OFFLINE";
  } else {
    renderStatus.textContent = `READY / ${mode.toUpperCase()}`;
  }
  return outcome;
}

function safeRefreshFromSource() {
  const generation = refreshGeneration;
  const source = selectedSource();
  const key = `${generation}:${panelType}:${source?.id ?? ""}`;
  if (activeRefresh?.key === key) {
    return activeRefresh.promise;
  }

  const promise = refreshFromSource(generation)
    .catch((error) => {
      if (generation === refreshGeneration) {
        sourceState.textContent = "ERROR";
        sourceNextRefresh.textContent = "--";
        renderStatus.textContent = "DATA REFRESH FAILED";
        console.error(error);
      }
      return null;
    })
    .finally(() => {
      if (activeRefresh?.promise === promise) {
        activeRefresh = null;
      }
    });
  activeRefresh = {key, promise};
  return promise;
}

function invalidateRefreshContext() {
  refreshGeneration += 1;
  currentData = null;
  activeRefresh = null;
}

function configureAutoRefresh({refreshNow = false} = {}) {
  if (autoRefreshTimer) {
    window.clearInterval(autoRefreshTimer);
    autoRefreshTimer = null;
  }
  autoOffButton.classList.toggle("active", !autoRefreshEnabled);
  autoOnButton.classList.toggle("active", autoRefreshEnabled);
  if (autoRefreshEnabled) {
    const intervalMilliseconds = Number(intervalSelect.value) * 1000;
    autoRefreshTimer = window.setInterval(safeRefreshFromSource, intervalMilliseconds);
  } else {
    sourceNextRefresh.textContent = "--";
  }
  if (refreshNow) {
    safeRefreshFromSource();
  }
}

async function setPanel(nextPanel) {
  invalidateRefreshContext();
  const generation = refreshGeneration;
  panelType = nextPanel;
  panelButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.panel === panelType);
  });
  panelTitle.textContent = `${panelType[0].toUpperCase()}${panelType.slice(1)}Panel`;
  preview.alt = `400×300 ${panelTitle.textContent} 预览`;
  renderStatus.textContent = "LOADING SOURCES";
  try {
    await Promise.all([loadSamples(nextPanel), loadDataSources(nextPanel)]);
    if (generation !== refreshGeneration || nextPanel !== panelType) {
      return;
    }
    configureAutoRefresh();
    await safeRefreshFromSource();
  } catch (error) {
    renderStatus.textContent = "PANEL LOAD FAILED";
    console.error(error);
  }
}

async function exportImage(format) {
  renderStatus.textContent = `EXPORTING ${format.toUpperCase()}`;
  try {
    const blob = await requestRender(format);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${panelType}-panel-${mode}.${format}`;
    link.click();
    URL.revokeObjectURL(url);
    renderStatus.textContent = `EXPORTED / ${format.toUpperCase()}`;
  } catch (error) {
    renderStatus.textContent = "EXPORT FAILED";
    console.error(error);
  }
}

async function initialize() {
  try {
    await Promise.all([loadSamples(), loadDataSources()]);
    await safeRefreshFromSource();
  } catch (error) {
    renderStatus.textContent = "INITIALIZATION FAILED";
    console.error(error);
  }
}

normalButton.addEventListener("click", () => setMode("normal"));
einkButton.addEventListener("click", () => setMode("eink"));
panelButtons.forEach((button) => {
  button.addEventListener("click", () => setPanel(button.dataset.panel));
});
refreshButton.addEventListener("click", safeRefreshFromSource);
pngButton.addEventListener("click", () => exportImage("png"));
bmpButton.addEventListener("click", () => exportImage("bmp"));
sampleSelect.addEventListener("change", () => {
  invalidateRefreshContext();
  safeRefreshFromSource();
});
sourceSelect.addEventListener("change", () => {
  invalidateRefreshContext();
  updateSourceControls();
  safeRefreshFromSource();
});
autoOffButton.addEventListener("click", () => {
  autoRefreshEnabled = false;
  configureAutoRefresh();
});
autoOnButton.addEventListener("click", () => {
  autoRefreshEnabled = true;
  configureAutoRefresh({refreshNow: true});
});
intervalSelect.addEventListener("change", () => {
  if (autoRefreshEnabled) {
    configureAutoRefresh({refreshNow: true});
  }
});

initialize();
