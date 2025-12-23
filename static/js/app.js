// Global state
let currentVideoData = null;
let currentTaskId = null;
let pollingInterval = null;

// DOM Elements
const urlInput = document.getElementById("urlInput");
const pasteBtn = document.getElementById("pasteBtn");
const checkBtn = document.getElementById("checkBtn");
const checkBtnText = document.getElementById("checkBtnText");
const checkBtnLoader = document.getElementById("checkBtnLoader");

const videoSection = document.getElementById("videoSection");
const sectionTitle = document.getElementById("sectionTitle");
const singleVideoView = document.getElementById("singleVideoView");
const playlistView = document.getElementById("playlistView");

const videoThumbnail = document.getElementById("videoThumbnail");
const videoTitle = document.getElementById("videoTitle");
const videoDuration = document.getElementById("videoDuration");

const playlistContainer = document.getElementById("playlistContainer");
const selectAllBtn = document.getElementById("selectAllBtn");
const deselectAllBtn = document.getElementById("deselectAllBtn");
const selectedCount = document.getElementById("selectedCount");

const downloadBtn = document.getElementById("downloadBtn");
const downloadBtnText = document.getElementById("downloadBtnText");
const downloadBtnLoader = document.getElementById("downloadBtnLoader");

const progressSection = document.getElementById("progressSection");
const progressFill = document.getElementById("progressFill");
const progressPercent = document.getElementById("progressPercent");
const progressText = document.getElementById("progressText");
const progressDetails = document.getElementById("progressDetails");

const resultSection = document.getElementById("resultSection");
const resultMessage = document.getElementById("resultMessage");
const downloadFileBtn = document.getElementById("downloadFileBtn");
const newDownloadBtn = document.getElementById("newDownloadBtn");

const errorSection = document.getElementById("errorSection");
const errorMessage = document.getElementById("errorMessage");
const retryBtn = document.getElementById("retryBtn");

// Utility Functions
function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  }
  return `${minutes}:${secs.toString().padStart(2, "0")}`;
}

function showSection(section) {
  [videoSection, progressSection, resultSection, errorSection].forEach((s) => {
    s.classList.add("hidden");
  });
  if (section) {
    section.classList.remove("hidden");
  }
}

function setButtonLoading(btn, textEl, loaderEl, isLoading) {
  btn.disabled = isLoading;
  if (isLoading) {
    textEl.classList.add("hidden");
    loaderEl.classList.remove("hidden");
  } else {
    textEl.classList.remove("hidden");
    loaderEl.classList.add("hidden");
  }
}

function showError(message) {
  errorMessage.textContent = message;
  showSection(errorSection);
}

// Event: Paste Button
pasteBtn.addEventListener("click", async () => {
  try {
    const text = await navigator.clipboard.readText();
    urlInput.value = text.trim();
    urlInput.focus();
  } catch (err) {
    // Fallback: show alert
    alert("Tidak bisa paste otomatis. Silakan paste manual dengan Ctrl+V");
    urlInput.focus();
  }
});

// Event: Check Video
checkBtn.addEventListener("click", async () => {
  const url = urlInput.value.trim();

  if (!url) {
    alert("Masukkan URL YouTube terlebih dahulu!");
    return;
  }

  setButtonLoading(checkBtn, checkBtnText, checkBtnLoader, true);
  showSection(null);

  try {
    const response = await fetch("/api/info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "URL tidak valid");
    }

    const data = await response.json();
    currentVideoData = data;

    displayVideoInfo(data);
    showSection(videoSection);
  } catch (error) {
    showError(error.message);
  } finally {
    setButtonLoading(checkBtn, checkBtnText, checkBtnLoader, false);
  }
});

// Display Video Info
function displayVideoInfo(data) {
  if (data.is_playlist) {
    // Playlist
    sectionTitle.textContent = `📋 ${data.playlist_title || "Playlist"} (${
      data.videos.length
    } video)`;
    singleVideoView.classList.add("hidden");
    playlistView.classList.remove("hidden");

    renderPlaylist(data.videos);
    updateSelectedCount();
  } else {
    // Single Video
    sectionTitle.textContent = "🎵 Video Ditemukan";
    playlistView.classList.add("hidden");
    singleVideoView.classList.remove("hidden");

    const video = data.videos[0];
    videoThumbnail.src = video.thumbnail;
    videoTitle.textContent = video.title;
    videoDuration.textContent = formatDuration(video.duration);
  }
}

// Render Playlist
function renderPlaylist(videos) {
    playlistContainer.innerHTML = '';
    
    videos.forEach(video => {
        const item = document.createElement('div');
        item.className = 'flex gap-3 p-3 bg-white border-2 border-purple-200 rounded-lg cursor-pointer hover:border-purple-500 transition-all';
        item.dataset.videoId = video.id;
        
        // Default thumbnail jika kosong
        const thumbnailUrl = video.thumbnail || `https://img.youtube.com/vi/${video.id}/mqdefault.jpg`;
        
        item.innerHTML = `
            <input type="checkbox" checked class="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500">
            <img src="${thumbnailUrl}" alt="" class="w-24 h-14 object-cover rounded-lg flex-shrink-0" onerror="this.src='https://img.youtube.com/vi/${video.id}/default.jpg'">
            <div class="flex-1 min-w-0">
                <h4 class="font-semibold text-gray-800 text-sm mb-1 line-clamp-2">${video.title}</h4>
                <span class="inline-block bg-gray-800 text-white text-xs px-2 py-1 rounded-full">${formatDuration(video.duration)}</span>
            </div>
        `;
        
        const checkbox = item.querySelector('input[type="checkbox"]');
        
        // Toggle on click
        item.addEventListener('click', (e) => {
            if (e.target.type !== 'checkbox') {
                checkbox.checked = !checkbox.checked;
            }
            updateItemStyle(item, checkbox.checked);
            updateSelectedCount();
        });
        
        checkbox.addEventListener('change', () => {
            updateItemStyle(item, checkbox.checked);
            updateSelectedCount();
        });
        
        playlistContainer.appendChild(item);
    });
}

function updateItemStyle(item, isChecked) {
  if (isChecked) {
    item.classList.remove("opacity-50");
    item.classList.add("border-purple-500", "bg-purple-50");
  } else {
    item.classList.add("opacity-50");
    item.classList.remove("border-purple-500", "bg-purple-50");
  }
}

// Select/Deselect All
selectAllBtn.addEventListener("click", () => {
  document.querySelectorAll("#playlistContainer > div").forEach((item) => {
    const checkbox = item.querySelector('input[type="checkbox"]');
    checkbox.checked = true;
    updateItemStyle(item, true);
  });
  updateSelectedCount();
});

deselectAllBtn.addEventListener("click", () => {
  document.querySelectorAll("#playlistContainer > div").forEach((item) => {
    const checkbox = item.querySelector('input[type="checkbox"]');
    checkbox.checked = false;
    updateItemStyle(item, false);
  });
  updateSelectedCount();
});

function updateSelectedCount() {
  const count = document.querySelectorAll(
    "#playlistContainer input:checked"
  ).length;
  selectedCount.textContent = `${count} video dipilih`;
}

// Event: Download
downloadBtn.addEventListener("click", async () => {
  if (!currentVideoData) return;

  setButtonLoading(downloadBtn, downloadBtnText, downloadBtnLoader, true);

  try {
    let response;

    if (currentVideoData.is_playlist) {
      // Get selected video IDs
      const selectedVideos = Array.from(
        document.querySelectorAll("#playlistContainer input:checked")
      ).map((checkbox) => checkbox.closest("div").dataset.videoId);

      if (selectedVideos.length === 0) {
        alert("Pilih minimal 1 video!");
        setButtonLoading(
          downloadBtn,
          downloadBtnText,
          downloadBtnLoader,
          false
        );
        return;
      }

      response = await fetch("/api/download-playlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: urlInput.value.trim(),
          video_ids: selectedVideos,
        }),
      });
    } else {
      // Single video
      response = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: urlInput.value.trim(),
        }),
      });
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Gagal memulai download");
    }

    const data = await response.json();
    currentTaskId = data.task_id;

    // Show progress and start polling
    showSection(progressSection);
    startPolling();
  } catch (error) {
    showError(error.message);
  } finally {
    setButtonLoading(downloadBtn, downloadBtnText, downloadBtnLoader, false);
  }
});

// Polling Task Status
function startPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval);
  }

  pollingInterval = setInterval(async () => {
    try {
      const response = await fetch(`/api/task/${currentTaskId}`);
      const data = await response.json();

      updateProgress(data);

      if (data.status === "completed") {
        clearInterval(pollingInterval);
        // Auto-trigger download
        triggerAutoDownload();
      } else if (data.status === "failed") {
        clearInterval(pollingInterval);
        showError(data.message);
      }
    } catch (error) {
      clearInterval(pollingInterval);
      showError("Gagal memeriksa status download");
    }
  }, 1000);
}

function updateProgress(data) {
  const percent = Math.round(data.progress);
  progressFill.style.width = `${percent}%`;
  progressPercent.textContent = `${percent}%`;
  progressText.textContent = data.message;

  if (data.total_videos > 1) {
    progressDetails.textContent = `${data.completed_videos} / ${data.total_videos} video selesai`;
    // Store for later use
    window.lastCompletedCount = data.completed_videos;
  } else {
    progressDetails.textContent = "";
  }
}

function triggerAutoDownload() {
  // For single video - direct download
  if (!currentVideoData.is_playlist || currentVideoData.videos.length === 1) {
    window.location.href = `/api/download-file/${currentTaskId}`;

    setTimeout(() => {
      resultMessage.textContent = "Video berhasil diconvert ke MP3!";
      showSection(resultSection);
    }, 1000);
  }
  // For playlist - open download page
  else {
    window.open(`/api/download-file/${currentTaskId}`, "_blank");

    // Use stored completed count
    const actualCompleted =
      window.lastCompletedCount || currentVideoData.videos.length;

    setTimeout(() => {
      resultMessage.textContent = `${actualCompleted} video berhasil didownload! Cek tab baru untuk download.`;
      showSection(resultSection);
    }, 500);
  }
}

// Download File (manual)
downloadFileBtn.addEventListener("click", () => {
  if (currentTaskId) {
    window.location.href = `/api/download-file/${currentTaskId}`;
  }
});

// New Download
newDownloadBtn.addEventListener("click", () => {
  urlInput.value = "";
  currentVideoData = null;
  currentTaskId = null;
  showSection(null);
  urlInput.focus();
});

// Retry
retryBtn.addEventListener("click", () => {
  showSection(null);
  if (currentVideoData) {
    displayVideoInfo(currentVideoData);
    showSection(videoSection);
  }
});

// Auto-focus on load
window.addEventListener("load", () => {
  urlInput.focus();
});

// Enter key to check video
urlInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    checkBtn.click();
  }
});
