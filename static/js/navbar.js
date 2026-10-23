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
        link.addEventListener("click", (e) => {
            if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
            const url = new URL(link.href, window.location.origin);
            const samePage = url.origin === window.location.origin && url.pathname === window.location.pathname;

            setOpen(false);

            if (samePage) {
                if (url.hash) {
                    e.preventDefault();
                    const target = document.querySelector(url.hash);
                    target?.scrollIntoView({ behavior: "smooth" });
                    history.replaceState(null, "", url.hash);
                } else {
                    e.preventDefault();
                }
            }
        });
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
})();
