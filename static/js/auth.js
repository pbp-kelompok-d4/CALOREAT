(function () {
  const page = document.querySelector(".auth-page");
  if (!page) return;

  const links = Array.from(page.querySelectorAll(".auth-toggle a[data-target]"));
  const panes = Array.from(page.querySelectorAll("[data-pane]"));

  function show(name, focusFirstField) {
    page.dataset.active = name;

    panes.forEach(function (pane) {
      const isActive = pane.dataset.pane === name;
      pane.classList.toggle("is-active", isActive);
      pane.setAttribute("aria-hidden", String(!isActive));
    });

    links.forEach(function (link) {
      const isActive = link.dataset.target === name;
      link.classList.toggle("is-active", isActive);
      if (isActive) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    });

    if (focusFirstField) {
      const input = page.querySelector('[data-pane="' + name + '"] input');
      if (input) input.focus({ preventScroll: true });
    }
  }

  // Simpan state awal supaya tombol Back/Forward bisa kembali ke tab ini
  history.replaceState({ authTab: page.dataset.active }, "");

  links.forEach(function (link) {
    link.addEventListener("click", function (event) {
      // Biarkan Ctrl/Cmd/Shift-click dan klik tengah membuka tab baru seperti biasa
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;

      event.preventDefault();
      const target = link.dataset.target;
      if (target === page.dataset.active) return;

      show(target, true);
      history.pushState({ authTab: target }, "", link.href);
    });
  });

  window.addEventListener("popstate", function (event) {
    if (event.state && event.state.authTab) {
      show(event.state.authTab, false);
    }
  });
})();