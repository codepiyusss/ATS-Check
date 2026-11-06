(function () {
  var MAX_BYTES = 5 * 1024 * 1024;
  var MIN_WORDS = 20;

  var form = document.getElementById("analyzeForm");
  if (!form) return;

  var tabs = Array.prototype.slice.call(form.querySelectorAll('[role="tab"]'));
  var panels = { "tab-upload": document.getElementById("panel-upload"), "tab-paste": document.getElementById("panel-paste") };
  var fileInput = document.getElementById("resume_file");
  var textArea = document.getElementById("resume_text");
  var dropZone = document.getElementById("dropZone");
  var fileName = document.getElementById("fileName");
  var errorBox = document.getElementById("resume-error");
  var jd = document.getElementById("job_description");
  var jdCount = document.getElementById("jdCount");
  var submitBtn = document.getElementById("submitBtn");
  var submitLabel = document.getElementById("submitLabel");
  var processing = document.getElementById("processing");

  function activeMode() {
    return tabs[0].getAttribute("aria-selected") === "true" ? "upload" : "paste";
  }

  // ---- Tabs (arrow keys, Home/End, roving tabindex) ----
  function selectTab(tab, focus) {
    tabs.forEach(function (t) {
      var on = t === tab;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
      panels[t.id].hidden = !on;
    });
    clearError();
    if (focus) tab.focus();
  }
  tabs.forEach(function (tab, i) {
    tab.addEventListener("click", function () { selectTab(tab, false); });
    tab.addEventListener("keydown", function (e) {
      var j = null;
      if (e.key === "ArrowRight") j = (i + 1) % tabs.length;
      else if (e.key === "ArrowLeft") j = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") j = 0;
      else if (e.key === "End") j = tabs.length - 1;
      if (j !== null) { e.preventDefault(); selectTab(tabs[j], true); }
    });
  });

  // ---- Errors (inline, announced by role="alert"; no alert() popups) ----
  function showError(message, field) {
    errorBox.querySelector("span").textContent = message;
    errorBox.classList.add("show");
    if (field) { field.setAttribute("aria-invalid", "true"); field.focus(); }
  }
  function clearError() {
    errorBox.classList.remove("show");
    errorBox.querySelector("span").textContent = "";
    fileInput.removeAttribute("aria-invalid");
    textArea.removeAttribute("aria-invalid");
  }

  // ---- File selection and drag-and-drop ----
  function isPdf(file) {
    return file.type === "application/pdf" || /\.pdf$/i.test(file.name);
  }
  function showFile() {
    var f = fileInput.files[0];
    fileName.textContent = f ? "Selected: " + f.name : "";
    clearError();
  }
  fileInput.addEventListener("change", showFile);

  ["dragenter", "dragover"].forEach(function (n) {
    dropZone.addEventListener(n, function (e) { e.preventDefault(); dropZone.classList.add("drag-over"); });
  });
  ["dragleave", "drop"].forEach(function (n) {
    dropZone.addEventListener(n, function (e) { e.preventDefault(); dropZone.classList.remove("drag-over"); });
  });
  dropZone.addEventListener("drop", function (e) {
    var files = e.dataTransfer && e.dataTransfer.files;
    if (!files || !files.length) return;
    if (!isPdf(files[0])) { showError("Only PDF files are supported.", null); return; }
    fileInput.files = files;
    showFile();
  });

  // ---- Job description counter ----
  if (jd && jdCount) {
    var count = function () { jdCount.textContent = String(jd.value.length); };
    jd.addEventListener("input", count); count();
  }

  // ---- Validate, then show a processing state ----
  form.addEventListener("submit", function (e) {
    clearError();
    if (activeMode() === "upload") {
      var f = fileInput.files[0];
      if (!f) { e.preventDefault(); showError("Choose a PDF file first, or switch to Paste text.", fileInput); return; }
      if (!isPdf(f)) { e.preventDefault(); showError("Only PDF files are supported.", fileInput); return; }
      if (f.size > MAX_BYTES) { e.preventDefault(); showError("That file is over the 5 MB limit. Please choose a smaller PDF.", fileInput); return; }
    } else {
      var words = textArea.value.trim().split(/\s+/).filter(Boolean).length;
      if (words < MIN_WORDS) { e.preventDefault(); showError("Please paste at least " + MIN_WORDS + " words of your resume.", textArea); return; }
    }

    // Only send the input the person is actually using.
    if (activeMode() === "upload") textArea.disabled = true; else fileInput.disabled = true;

    submitBtn.setAttribute("aria-busy", "true");
    submitBtn.disabled = true;
    submitLabel.textContent = "Analyzing...";
    processing.textContent = "Analyzing your resume. This usually takes a few seconds.";
  });

  // Back/forward cache: restore the form if the person returns to this page.
  window.addEventListener("pageshow", function (e) {
    if (!e.persisted) return;
    textArea.disabled = false; fileInput.disabled = false;
    submitBtn.removeAttribute("aria-busy"); submitBtn.disabled = false;
    submitLabel.textContent = "Analyze resume"; processing.textContent = "";
  });
})();
