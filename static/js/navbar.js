(() => {
    const toggle = document.getElementById("nav-toggle");
    const icon = document.getElementById("nav-icon4");
    const drawer = document.getElementById("nav-mobile-drawer");
    if (!toggle || !icon || !drawer) return;

    let isOpen = false;
    const setOpen = (open) => {
        isOpen = open;
        icon.classList.toggle("active", open);
        drawer.classList.toggle("is-open", open);
        drawer.setAttribute("aria-hidden", String(!open));
        toggle.setAttribute("aria-expanded", String(open));
        document.body.classList.toggle("nav-open", open);
    };

    toggle.addEventListener("click", () => setOpen(!isOpen));

    drawer.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => setOpen(false));
    });

    document.getElementById("nav-profile-setup-mobile")?.addEventListener("click", () => {
        setOpen(false);
        document.getElementById("nav-profile-setup")?.click();
    });

    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && isOpen) setOpen(false);
    });
    window.addEventListener("resize", () => {
        if (window.innerWidth > 768 && isOpen) setOpen(false);
    });

    // Close navbar when scrolling down
    const nav = document.querySelector(".nav");
    let lastScrollY = window.scrollY;

    window.addEventListener("scroll", () => {
        if (!nav || isOpen) return;
        const currentScrollY = window.scrollY;
        const delta = currentScrollY - lastScrollY;

        if (currentScrollY <= 60) {
            // Always show when near the very top of the page
            nav.classList.remove("nav--hidden");
        } else if (delta > 6) {
            // Scrolling down
            nav.classList.add("nav--hidden");
        } else if (delta < -6) {
            // Scrolling up
            nav.classList.remove("nav--hidden");
        }
        lastScrollY = currentScrollY;
    }, { passive: true });
})();
