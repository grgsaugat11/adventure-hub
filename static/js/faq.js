document.querySelectorAll("details.faq__item").forEach(item => {
  item.addEventListener("toggle", () => {
    if (!item.open) return;
    document.querySelectorAll("details.faq__item").forEach(other => {
      if (other !== item) other.open = false;
    });
  });
});
