(() => {
  const sortSelect = document.querySelector("[data-sort-select]");
  sortSelect?.addEventListener("change", () => sortSelect.form?.requestSubmit());
  window.AdventureUI?.drawer({
    panel: document.querySelector("#adventure-filters"),
    trigger: document.querySelector("[data-filter-toggle]"),
    closeButton: document.querySelector("[data-filter-close]"),
    backdrop: document.querySelector("[data-filter-backdrop]"),
    panelClass: "is-open",
    backdropClass: "is-visible",
    breakpoint: "(max-width: 992px)",
  });
})();
