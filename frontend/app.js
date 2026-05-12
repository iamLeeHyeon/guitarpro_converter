// frontend/app.js
const API_BASE = "http://localhost:8000";

const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const fileInfo = document.getElementById("fileInfo");
const fileName = document.getElementById("fileName");
const formatSelect = document.getElementById("formatSelect");
const convertBtn = document.getElementById("convertBtn");
const progress = document.getElementById("progress");
const errorBox = document.getElementById("errorBox");
const downloadBtn = document.getElementById("downloadBtn");

let selectedFile = null;
let selectedFormat = "gp5";

// 드래그앤드롭
dropZone.addEventListener("click", () => fileInput.click());
dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("drag-over"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", e => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
});
fileInput.addEventListener("change", () => { if (fileInput.files[0]) setFile(fileInput.files[0]); });

// 포맷 선택
formatSelect.querySelectorAll(".fmt-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    formatSelect.querySelectorAll(".fmt-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    selectedFormat = btn.dataset.fmt;
  });
});

function setFile(file) {
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    showError("PDF 파일만 업로드 가능합니다.");
    return;
  }
  selectedFile = file;
  fileName.textContent = file.name;
  fileInfo.classList.remove("hidden");
  convertBtn.classList.remove("hidden");
  errorBox.classList.add("hidden");
  downloadBtn.classList.add("hidden");
}

convertBtn.addEventListener("click", async () => {
  if (!selectedFile) return;
  setState("converting");

  const formData = new FormData();
  formData.append("file", selectedFile);
  formData.append("format", selectedFormat);

  try {
    const res = await fetch(`${API_BASE}/convert`, { method: "POST", body: formData });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "변환 실패");
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const stem = selectedFile.name.replace(/\.pdf$/i, "");
    downloadBtn.href = url;
    downloadBtn.download = `${stem}.${selectedFormat}`;
    setState("done");
  } catch (e) {
    showError(e.message);
    setState("idle");
  }
});

function setState(state) {
  progress.classList.toggle("hidden", state !== "converting");
  downloadBtn.classList.toggle("hidden", state !== "done");
  convertBtn.disabled = state === "converting";
}

function showError(msg) {
  errorBox.textContent = msg;
  errorBox.classList.remove("hidden");
}
