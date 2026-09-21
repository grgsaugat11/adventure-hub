const heroImage = document.querySelector(".hero__image");

if (heroImage) {

    heroImage.addEventListener("mousemove", (e) => {

        const rect = heroImage.getBoundingClientRect();

        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateY = ((x - centerX) / centerX) * 10;
        const rotateX = ((centerY - y) / centerY) * 10;

        heroImage.style.transform =
            `perspective(1000px)
             rotateX(${rotateX}deg)
             rotateY(${rotateY}deg)`;

    });

    heroImage.addEventListener("mouseleave", () => {

        heroImage.style.transform =
            "perspective(1000px) rotateX(0deg) rotateY(0deg)";

    });

}

/* ======================================
   FEATURED ADVENTURES SLIDER
====================================== */

(() => {

    const slider = document.querySelector("[data-carousel]");

    if (!slider) return;

    const track = slider.querySelector("[data-carousel-track]");

    const slides = [...slider.querySelectorAll("[data-carousel-slide]")];

    const prevBtn = slider.querySelector("[data-carousel-prev]");

    const nextBtn = slider.querySelector("[data-carousel-next]");

    const dotsWrap = slider.querySelector("[data-carousel-dots]");

    if (!track || slides.length < 2) return;

    const reduceMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    const AUTOPLAY_MS = 5000;

    let index = 0;

    let autoplayTimer = null;

    let resizeTimer = null;

    const dots = slides.map((_, i) => {

        const dot = document.createElement("button");

        dot.type = "button";

        dot.className = "featured__dot";

        dot.setAttribute("role", "tab");

        dot.setAttribute("aria-label", `Show adventure ${i + 1} of ${slides.length}`);

        dot.addEventListener("click", () => {

            go(i);

            restart();

        });

        dotsWrap.appendChild(dot);

        return dot;

    });

    const gapWidth = () =>
        parseFloat(getComputedStyle(track).gap) || 0;

    const slideWidth = () =>
        slides[0].offsetWidth;

    const viewportWidth = () =>
        track.parentElement.clientWidth;

    const offsetFor = (i) => {
        const gap = gapWidth();
        const width = slideWidth();
        const start = (viewportWidth() - width) / 2;
        return start - i * (width + gap);
    };

    const update = () => {
        track.style.transform = `translateX(${offsetFor(index)}px)`;
        slides.forEach((slide, i) => {
            slide.classList.toggle("is-active", i === index);
        });
        dots.forEach((dot, i) => {
            dot.classList.toggle("is-active", i === index);
            dot.setAttribute("aria-selected", i === index ? "true" : "false");
        });
    };

    const go = (i) => {
        index = ((i % slides.length) + slides.length) % slides.length;
        update();
    };

    const next = () => go(index + 1);

    const prev = () => go(index - 1);

    const play = () => {
        if (reduceMotion) return;
        stop();
        autoplayTimer = setInterval(next, AUTOPLAY_MS);
    };

    const stop = () => {
        if (autoplayTimer) {
            clearInterval(autoplayTimer);
            autoplayTimer = null;
        }
    };

    const restart = () => {
        stop();
        play();
    };

    prevBtn && prevBtn.addEventListener("click", () => { prev(); restart(); });

    nextBtn && nextBtn.addEventListener("click", () => { next(); restart(); });

    slider.addEventListener("mouseenter", stop);

    slider.addEventListener("mouseleave", play);

    slider.addEventListener("focusin", stop);

    slider.addEventListener("focusout", play);

    window.addEventListener("resize", () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(update, 120);
    });

    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(update);
    }

    update();

    play();

})();