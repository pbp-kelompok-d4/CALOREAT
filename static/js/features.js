document.querySelectorAll(".features").forEach((features) => {
  const list = features.querySelector(".features__list");
  const toggle = features.querySelector(".features__toggle");

  if (!list || !toggle) return;

  const updateListHeight = () => {
    features.style.setProperty("--features-list-height", `${list.scrollHeight}px`);
  };

  updateListHeight();
  toggle.addEventListener("click", () => {
    const isCollapsed = features.classList.toggle("is-collapsed");
    toggle.setAttribute("aria-expanded", String(!isCollapsed));
    toggle.setAttribute("aria-label", isCollapsed ? "Expand features" : "Collapse features");
  });
  window.addEventListener("resize", updateListHeight);
});
