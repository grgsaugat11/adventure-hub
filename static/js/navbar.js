window.AdventureUI?.drawer({
  panel: document.querySelector(".mobile-menu"),
  trigger: document.querySelector(".nav-toggle"),
  closeButton: document.querySelector(".mobile-menu__close"),
  backdrop: document.querySelector(".mobile-overlay"),
  panelClass: "active",
  backdropClass: "active",
  breakpoint: "(max-width: 1200px)",
  alwaysHidden: true,
});
