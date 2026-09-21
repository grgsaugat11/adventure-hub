const sortSelect = document.querySelector("[data-sort-select]");
const filters = document.querySelector("#adventure-filters");
const filtersToggle = document.querySelector("[data-filter-toggle]");
const filtersClose = document.querySelector("[data-filter-close]");
const filtersBackdrop = document.querySelector("[data-filter-backdrop]");

function openFilters() {
  filters.classList.add("is-open");
  filtersBackdrop.classList.add("is-visible");
  document.body.style.overflow = "hidden";
}

function closeFilters() {
  filters.classList.remove("is-open");
  filtersBackdrop.classList.remove("is-visible");
  document.body.style.overflow = "";
}

if (sortSelect) {
  sortSelect.addEventListener("change", () => {
    sortSelect.form?.submit();
  });
}

if (filtersToggle && filters) {
  filtersToggle.addEventListener("click", openFilters);
  filtersClose?.addEventListener("click", closeFilters);
  filtersBackdrop?.addEventListener("click", closeFilters);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeFilters();
    }
  });
}