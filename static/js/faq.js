const faqItems = document.querySelectorAll(".faq__item");

faqItems.forEach(item => {

    const button = item.querySelector(".faq__question");

    button.addEventListener("click", () => {

        faqItems.forEach(faq => {

            if (faq !== item) {
                faq.classList.remove("active");
            }

        });

        item.classList.toggle("active");

    });

});