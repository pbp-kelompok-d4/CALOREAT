function setupCollapsible(containerSelector, contentSelector, toggleSelector, varName, labelPrefix) {
	document.querySelectorAll(containerSelector).forEach((container) => {
		const content = container.querySelector(contentSelector);
		const toggle = container.querySelector(toggleSelector);

		if (!content || !toggle) return;

		const updateHeight = () => {
			if (!container.classList.contains("is-collapsed")) {
				container.style.setProperty(varName, `${content.scrollHeight}px`);
			}
		};

		updateHeight();
		const observer = new MutationObserver(updateHeight);
		observer.observe(content, { childList: true, subtree: true, attributes: true });

		toggle.addEventListener("click", () => {
			updateHeight();
			const isCollapsed = container.classList.toggle("is-collapsed");
			toggle.setAttribute("aria-expanded", String(!isCollapsed));
			toggle.setAttribute("aria-label", isCollapsed ? `Expand ${labelPrefix}` : `Collapse ${labelPrefix}`);
		});
		window.addEventListener("resize", updateHeight);
	});
}

setupCollapsible(".features", ".features__list", ".features__toggle", "--features-list-height", "features");
setupCollapsible(".dashboard-education", ".dashboard-content", ".features__toggle", "--education-content-height", "education");
setupCollapsible(".dashboard-reviews", ".dashboard-reviews-body", ".features__toggle", "--reviews-content-height", "reviews");
