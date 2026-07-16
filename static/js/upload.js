// Handles the "Upload Resume" / "Paste Resume Text" tabs and the
// drag-and-drop upload box on the homepage.

document.addEventListener("DOMContentLoaded", function () {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      const targetId = btn.getAttribute("data-tab");

      tabButtons.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      document.getElementById(targetId).classList.add("active");
    });
  });

  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("resume_file");
  const fileNameDisplay = document.getElementById("fileNameDisplay");

  if (!dropZone || !fileInput) return;

  function showFileName(file) {
    if (file) {
      fileNameDisplay.textContent = "Selected: " + file.name;
    } else {
      fileNameDisplay.textContent = "";
    }
  }

  fileInput.addEventListener("change", function () {
    showFileName(fileInput.files[0]);
  });

  // Drag and drop support
  ["dragenter", "dragover"].forEach(function (eventName) {
    dropZone.addEventListener(eventName, function (e) {
      e.preventDefault();
      dropZone.classList.add("drag-over");
    });
  });

  ["dragleave", "drop"].forEach(function (eventName) {
    dropZone.addEventListener(eventName, function (e) {
      e.preventDefault();
      dropZone.classList.remove("drag-over");
    });
  });

  dropZone.addEventListener("drop", function (e) {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];

      if (file.type !== "application/pdf") {
        alert("Only PDF files are supported.");
        return;
      }

      fileInput.files = files;
      showFileName(file);
    }
  });

  // Basic client-side check before submitting the form
  const form = document.getElementById("analyzeForm");
  if (form) {
    form.addEventListener("submit", function (e) {
      const pasteTab = document.getElementById("paste-tab");
      const resumeTextArea = document.getElementById("resume_text");
      const hasFile = fileInput.files.length > 0;
      const hasPastedText = resumeTextArea && resumeTextArea.value.trim().length > 0;

      if (!hasFile && !hasPastedText) {
        e.preventDefault();
        alert("Please upload a PDF or paste your resume text before analyzing.");
        return;
      }

      if (hasFile) {
        const file = fileInput.files[0];
        const maxSizeBytes = 5 * 1024 * 1024;
        if (file.size > maxSizeBytes) {
          e.preventDefault();
          alert("File is too large. Maximum size is 5 MB.");
        }
      }
    });
  }
});
