// Simple mobile navbar toggle.
// Nothing fancy - just show/hide the nav links on small screens.

document.addEventListener("DOMContentLoaded", function () {
  const toggleBtn = document.getElementById("navToggle");
  const navLinks = document.getElementById("navLinks");

  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener("click", function () {
      navLinks.classList.toggle("open");
    });
  }
});
