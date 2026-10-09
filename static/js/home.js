(() => {
  const slider = document.querySelector("[data-carousel]");
  if (!slider) return;
  const track = slider.querySelector("[data-carousel-track]");
  const slides = [...slider.querySelectorAll("[data-carousel-slide]")];
  const previous = slider.querySelector("[data-carousel-prev]");
  const next = slider.querySelector("[data-carousel-next]");
  const dotsContainer = slider.querySelector("[data-carousel-dots]");
  if (!track || !slides.length || !dotsContainer) return;
  let index = 0;
  const dots = slides.map((_, position) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.className = "featured__dot";
    dot.setAttribute("aria-label", `Show adventure ${position + 1} of ${slides.length}`);
    dot.addEventListener("click", () => go(position));
    dotsContainer.append(dot);
    return dot;
  });

  function update() {
    const gap = parseFloat(getComputedStyle(track).gap) || 0;
    const width = slides[0].offsetWidth;
    const offset = (track.parentElement.clientWidth - width) / 2 - index * (width + gap);
    track.style.transform = `translateX(${offset}px)`;
    slides.forEach((slide, position) => {
      slide.classList.toggle("is-active", position === index);
      slide.inert = position !== index;
    });
    dots.forEach((dot, position) => {
      dot.classList.toggle("is-active", position === index);
      dot.setAttribute("aria-pressed", String(position === index));
    });
  }

  function go(position) {
    index = (position + slides.length) % slides.length;
    update();
  }
  previous?.addEventListener("click", () => go(index - 1));
  next?.addEventListener("click", () => go(index + 1));
  if (slides.length === 1) {
    if (previous) previous.hidden = true;
    if (next) next.hidden = true;
    dotsContainer.hidden = true;
  }
  if (window.ResizeObserver) new ResizeObserver(update).observe(slider);
  else window.addEventListener("resize", update);
  document.fonts?.ready.then(update);
  update();
})();
