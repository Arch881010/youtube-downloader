const form = document.getElementById("downloadForm");
const urlInput = document.getElementById("urlInput");
const keyInput = document.getElementById("key");
const modeSelect = document.getElementById("modeSelect");
const statusText = document.getElementById("statusText");
const expiresText = document.getElementById("expiresText");
const downloadLink = document.getElementById("downloadLink");
const deleteButton = document.getElementById("deleteButton");
const previewCard = document.getElementById("previewCard");
const videoPreview = document.getElementById("videoPreview");
const audioPreview = document.getElementById("audioPreview");
const startButton = document.getElementById("startButton");

let activeJobId = null;
let pollTimer = null;
let activePreviewUrl = "";

function setStatus(message) {
  statusText.textContent = message;
}

function shouldPoll(status) {
  return status === "queued" || status === "downloading";
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

function clearPreview() {
  activePreviewUrl = "";

  previewCard.hidden = true;

  videoPreview.pause();
  audioPreview.pause();

  videoPreview.hidden = true;
  audioPreview.hidden = true;

  videoPreview.removeAttribute("src");
  audioPreview.removeAttribute("src");

  videoPreview.load();
  audioPreview.load();
}

function setPreview(mode, previewUrl) {
  previewCard.hidden = false;

  if (previewUrl !== activePreviewUrl) {
    activePreviewUrl = previewUrl;
    videoPreview.pause();
    audioPreview.pause();

    if (mode === "audio") {
      audioPreview.src = previewUrl;
      audioPreview.hidden = false;
      videoPreview.hidden = true;
      videoPreview.removeAttribute("src");
      videoPreview.load();
      audioPreview.load();
      return;
    }

    videoPreview.src = previewUrl;
    videoPreview.hidden = false;
    audioPreview.hidden = true;
    audioPreview.removeAttribute("src");
    audioPreview.load();
    videoPreview.load();
    return;
  }

  if (mode === "audio") {
    audioPreview.hidden = false;
    videoPreview.hidden = true;
  } else {
    videoPreview.hidden = false;
    audioPreview.hidden = true;
  }
}

async function apiRequest(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMessage = data.error || "Request failed";
    throw new Error(errorMessage);
  }

  return data;
}

function formatDate(isoDateString) {
  if (!isoDateString) {
    return "";
  }

  const date = new Date(isoDateString);
  return date.toLocaleString();
}

function renderJob(job) {
  const currentStatus = job.status;

  if (job.downloadUrl) {
    downloadLink.hidden = false;
    downloadLink.href = job.downloadUrl;
    downloadLink.textContent = "Download File";
  } else {
    downloadLink.hidden = true;
  }

  if (currentStatus === "completed") {
    deleteButton.hidden = false;
  } else {
    deleteButton.hidden = true;
  }

  if (job.previewUrl && currentStatus === "completed") {
    setPreview(job.mode, job.previewUrl);
  } else {
    clearPreview();
  }

  if (job.expiresAt) {
    expiresText.textContent = `Auto-delete: ${formatDate(job.expiresAt)}`;
  } else if (job.deletedAt) {
    expiresText.textContent = `Deleted: ${formatDate(job.deletedAt)} (${job.deleteReason || "unknown"})`;
  } else {
    expiresText.textContent = "";
  }

  if (currentStatus === "queued") {
    setStatus("Queued...");
    return;
  }

  if (currentStatus === "downloading") {
    setStatus("Downloading...");
    return;
  }

  if (currentStatus === "completed") {
    setStatus("Download complete. Preview it, then choose Download or Delete.");
    stopPolling();
    return;
  }

  if (currentStatus === "deleted") {
    setStatus("File was removed from server.");
    stopPolling();
    return;
  }

  if (currentStatus === "failed") {
    setStatus(`Download failed: ${job.error || "Unknown error"}`);
    stopPolling();
    return;
  }

  setStatus(`Current status: ${currentStatus}`);
}

async function refreshJob(jobId) {
  try {
    const job = await apiRequest(`/api/jobs/${jobId}`);
    renderJob(job);
  } catch (error) {
    setStatus(`Status error: ${error.message}`);
    stopPolling();
  }
}

async function startDownload(event) {
  event.preventDefault();

  const url = urlInput.value.trim();
  const key = keyInput ? keyInput.value.trim() : "";
  const mode = modeSelect.value;

  if (!url) {
    setStatus("Please enter a URL.");
    return;
  }

  if (!key) {
    setStatus("Please enter your key.");
    return;
  }

  setStatus("Starting request...")

  startButton.disabled = true;
  stopPolling();
  deleteButton.hidden = true;
  downloadLink.hidden = true;
  expiresText.textContent = "";
  clearPreview();

  try {
    const job = await apiRequest("/api/download", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Api-Key": key,
      },
      body: JSON.stringify({ url, mode, key }),
    });

    activeJobId = job.id;

    if (job.reused && job.status === "completed") {
      setStatus(`Using existing file for video ID ${activeJobId}.`);
    } else if (job.reused) {
      setStatus(`Video ID ${activeJobId} is already downloading.`);
    } else {
      setStatus(`Started download for video ID ${activeJobId}.`);
    }

    renderJob(job);

    if (shouldPoll(job.status)) {
      pollTimer = setInterval(() => {
        if (activeJobId) {
          refreshJob(activeJobId);
        }
      }, 1500);
    }
  } catch (error) {
    setStatus(`Could not start download: ${error.message}`);
  } finally {
    startButton.disabled = false;
  }
}

form.addEventListener("submit", startDownload);

downloadLink.addEventListener("click", () => {
  setStatus("Download started. File is removed automatically after transfer or in 30 minutes.");
});

async function deleteCurrentJob() {
  if (!activeJobId) {
    return;
  }

  // Stop media playback first to reduce "file in use" errors on delete.
  clearPreview();
  deleteButton.disabled = true;

  try {
    const job = await apiRequest(`/api/jobs/${activeJobId}/delete`, {
      method: "POST",
    });
    renderJob(job);
    setStatus("File deleted from server.");
  } catch (error) {
    setStatus(`Delete failed: ${error.message}`);
  } finally {
    deleteButton.disabled = false;
  }
}

deleteButton.addEventListener("click", deleteCurrentJob);
