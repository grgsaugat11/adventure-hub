const navToggle = document.querySelector(".nav-toggle");
const mobileMenu = document.querySelector(".mobile-menu");
const mobileOverlay = document.querySelector(".mobile-overlay");
const closeButton = document.querySelector(".mobile-menu__close");

function openMenu() {
  mobileMenu.classList.add("active");
  mobileOverlay.classList.add("active");
  document.body.classList.add("menu-open");
}

function closeMenu() {
  mobileMenu.classList.remove("active");
  mobileOverlay.classList.remove("active");
  document.body.classList.remove("menu-open");
}

navToggle.addEventListener("click", openMenu);

closeButton.addEventListener("click", closeMenu);

mobileOverlay.addEventListener("click", closeMenu);

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeMenu();
  }
});
