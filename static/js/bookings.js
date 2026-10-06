(() => {
  const form = document.querySelector("[data-booking-form]");
  const summary = document.querySelector("[data-booking-summary]");
  if (!form || !summary) return;
  const travellers = form.querySelector('[name="travellers"]');
  const output = summary.querySelector("[data-booking-total]");
  const price = Number(summary.dataset.price);
  function updateTotal() {
    const count = Number(travellers.value);
    output.textContent = Number.isInteger(count) && count > 0 && count <= Number(travellers.max)
      ? `${summary.dataset.currency} ${(price * count).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
      : "Choose a valid group size";
  }
  travellers.addEventListener("input", updateTotal);
  updateTotal();
})();
