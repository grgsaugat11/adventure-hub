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