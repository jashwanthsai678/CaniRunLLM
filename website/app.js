(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", () => {
    const tabs = document.querySelectorAll(".install-tab");
    const panels = document.querySelectorAll(".install-panel");

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        tabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");

        panels.forEach((panel) => {
          panel.hidden = panel.dataset.panel !== tab.dataset.tab;
        });
      });
    });
  });
})();
