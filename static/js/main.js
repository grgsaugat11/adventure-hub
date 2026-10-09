(() => {
  if (window.lucide) window.lucide.createIcons();

  // Shared keyboard behavior for the navigation and catalog filter drawers.
  window.AdventureUI = {
    drawer({ panel, trigger, closeButton, backdrop, panelClass, backdropClass, breakpoint, alwaysHidden = false }) {
      if (!panel || !trigger || !closeButton || !backdrop) return;
      const mobile = window.matchMedia(breakpoint);
      let isOpen = false;
      let previousFocus;
      let inertSiblings = [];
      const focusable = () => [...panel.querySelectorAll('a[href], button:not(:disabled), input:not(:disabled), select:not(:disabled), [tabindex="0"]')]
        .filter(element => element.getClientRects().length > 0 && getComputedStyle(element).visibility !== "hidden" && !element.closest("[inert]"));

      function close(restoreFocus = true) {
        if (!isOpen) return;
        isOpen = false;
        panel.classList.remove(panelClass);
        backdrop.classList.remove(backdropClass);
        panel.removeAttribute("role");
        panel.removeAttribute("aria-modal");
        trigger.setAttribute("aria-expanded", "false");
        document.body.classList.remove("drawer-open");
        inertSiblings.forEach(([element, wasInert]) => { element.inert = wasInert; });
        inertSiblings = [];
        if (restoreFocus && previousFocus?.isConnected) previousFocus.focus();
        panel.inert = alwaysHidden || mobile.matches;
      }

      function open() {
        if (isOpen || !mobile.matches) return;
        previousFocus = document.activeElement;
        isOpen = true;
        panel.inert = false;
        panel.classList.add(panelClass);
        backdrop.classList.add(backdropClass);
        panel.setAttribute("role", "dialog");
        panel.setAttribute("aria-modal", "true");
        trigger.setAttribute("aria-expanded", "true");
        document.body.classList.add("drawer-open");
        closeButton.focus();
        // Isolate siblings at each ancestor level, including nested sidebars.
        for (let node = panel; node.parentElement; node = node.parentElement) {
          [...node.parentElement.children].forEach(element => {
            if (element !== node && element !== backdrop && !["SCRIPT", "STYLE", "LINK"].includes(element.tagName)) {
              inertSiblings.push([element, element.inert]);
              element.inert = true;
            }
          });
          if (node.parentElement === document.body) break;
        }
      }

      trigger.addEventListener("click", open);
      closeButton.addEventListener("click", () => close());
      backdrop.addEventListener("click", () => close());
      panel.addEventListener("keydown", event => {
        if (!isOpen) return;
        if (event.key === "Escape") { event.preventDefault(); close(); }
        if (event.key === "Tab") {
          const items = focusable();
          const first = items[0], last = items.at(-1);
          if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
          else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
        }
      });
      const sync = () => {
        close(false);
        panel.inert = alwaysHidden || mobile.matches;
      };
      mobile.addEventListener("change", sync);
      sync();
    }
  };

  document.querySelectorAll('form.site-form[method="post"]').forEach(form => {
    const buttons = [...form.querySelectorAll('button[type="submit"]')];
    const feedback = document.createElement("p");
    feedback.className = "submission-status";
    feedback.setAttribute("role", "status");
    let submitting = false;
    form.addEventListener("submit", event => {
      if (event.defaultPrevented) return;
      if (submitting) { event.preventDefault(); return; }
      submitting = true;
      buttons.forEach(button => { button.disabled = true; });
      form.setAttribute("aria-busy", "true");
      feedback.textContent = "Submitting, please wait…";
      form.append(feedback);
    });
    // Browsers may restore disabled controls when navigating back.
    window.addEventListener("pageshow", () => {
      submitting = false;
      buttons.forEach(button => { button.disabled = false; });
      form.removeAttribute("aria-busy");
      feedback.remove();
    });
  });
})();
