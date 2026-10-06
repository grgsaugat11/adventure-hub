(() => {
  const photos = Array.from(document.querySelectorAll("[data-gallery-photo]"));
  const dialog = document.querySelector("[data-gallery-dialog]");
  if (!dialog || !photos.length || typeof dialog.showModal !== "function") return;
  let index = 0;
  function showPhoto(nextIndex) {
    index = (nextIndex + photos.length) % photos.length;
    const photo = photos[index];
    const image = dialog.querySelector("[data-gallery-preview]");
    image.src = photo.dataset.src;
    image.alt = photo.dataset.alt;
    dialog.querySelector("[data-gallery-title]").textContent = photo.dataset.title;
    dialog.querySelector("[data-gallery-caption]").textContent = photo.dataset.caption;
    dialog.querySelector("[data-gallery-counter]").textContent = `${index + 1} / ${photos.length}`;
    dialog.querySelector("[data-gallery-prev]").disabled = photos.length === 1;
    dialog.querySelector("[data-gallery-next]").disabled = photos.length === 1;
  }
  photos.forEach((photo, photoIndex) => photo.addEventListener("click", () => {
    showPhoto(photoIndex);
    dialog.showModal();
  }));
  dialog.querySelector("[data-gallery-close]").addEventListener("click", () => dialog.close());
  dialog.querySelector("[data-gallery-prev]").addEventListener("click", () => showPhoto(index - 1));
  dialog.querySelector("[data-gallery-next]").addEventListener("click", () => showPhoto(index + 1));
  dialog.addEventListener("keydown", event => {
    if (event.key === "ArrowLeft") { event.preventDefault(); showPhoto(index - 1); }
    if (event.key === "ArrowRight") { event.preventDefault(); showPhoto(index + 1); }
  });
  dialog.addEventListener("click", event => {
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  });
})();
