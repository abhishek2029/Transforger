const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const transformBtn = document.getElementById("transformBtn");
const status = document.getElementById("status");
const btnText = transformBtn.querySelector(".btn-text");
const btnLoading = transformBtn.querySelector(".btn-loading");
const outputBucket = document.getElementById("outputBucket");
const outputHint = document.getElementById("outputHint");
const downloadBtn = document.getElementById("downloadBtn");

let selectedFile = null;
let downloadUrl = null;

// Drag and drop
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");
  const file = e.dataTransfer.files[0];
  if (file && (file.name.endsWith(".docx") || file.name.endsWith(".pdf"))) {
    setFile(file);
  } else {
    showStatus("Please upload a .docx or .pdf file", "error");
  }
});

dropZone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) {
    setFile(fileInput.files[0]);
  }
});

function setFile(file) {
  selectedFile = file;
  fileName.textContent = file.name;
  dropZone.classList.add("has-file");
  transformBtn.disabled = false;
  status.hidden = true;
  // Reset output
  resetOutput();
}

function resetOutput() {
  outputBucket.classList.remove("ready");
  outputHint.textContent = "Waiting for transformation...";
  downloadBtn.hidden = true;
  if (downloadUrl) {
    URL.revokeObjectURL(downloadUrl);
    downloadUrl = null;
  }
}

function showStatus(msg, type) {
  status.textContent = msg;
  status.className = `status ${type}`;
  status.hidden = false;
}

transformBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  btnText.hidden = true;
  btnLoading.hidden = false;
  transformBtn.disabled = true;
  status.hidden = true;
  resetOutput();
  outputHint.textContent = "Transforming...";

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const res = await fetch("/transform", { method: "POST", body: formData });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Transformation failed");
    }

    const blob = await res.blob();
    downloadUrl = URL.createObjectURL(blob);

    // Get filename from Content-Disposition header or default
    const disposition = res.headers.get("Content-Disposition") || "";
    const fnMatch = disposition.match(/filename="?([^";\n]+)"?/);
    const outputName = fnMatch ? fnMatch[1] : "transformed_report.docx";

    // Show output bucket as ready
    outputBucket.classList.add("ready");
    outputHint.textContent = outputName;
    downloadBtn.href = downloadUrl;
    downloadBtn.download = outputName;
    downloadBtn.hidden = false;

    showStatus("Transformation complete. Download your report from the Output Bucket.", "success");
  } catch (err) {
    outputHint.textContent = "Transformation failed";
    showStatus(err.message, "error");
  } finally {
    btnText.hidden = false;
    btnLoading.hidden = true;
    transformBtn.disabled = false;
  }
});
