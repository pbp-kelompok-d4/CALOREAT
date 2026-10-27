
document.addEventListener("DOMContentLoaded", () => {
    const filterForm = document.getElementById("portion-guidance-filter");
    const mealSelect = document.getElementById("meal_type");
    const resultsContainer = document.getElementById(
        "portion-guidance-results"
    );

    if (!filterForm || !mealSelect || !resultsContainer) {
        return;
    }

    let activeController = null;

    async function filterPortionGuides() {
        if (activeController) {
            activeController.abort();
        }

        activeController = new AbortController();

        const params = new URLSearchParams(new FormData(filterForm));
        const url = `${filterForm.action}?${params.toString()}`;

        resultsContainer.setAttribute("aria-busy", "true");

        try {
            const response = await fetch(url, {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
                signal: activeController.signal,
            });

            if (!response.ok) {
                throw new Error("Failed to load portion guides.");
            }

            const html = await response.text();
            resultsContainer.innerHTML = html;

            // Keep the selected filter in the browser URL.
            window.history.replaceState({}, "", url);
        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }

            console.error("Error filtering portion guides:", error);

            // Fall back to the regular server-rendered page.
            filterForm.submit();
        } finally {
            resultsContainer.removeAttribute("aria-busy");
        }
    }

    mealSelect.addEventListener("change", filterPortionGuides);

    filterForm.addEventListener("submit", (event) => {
        event.preventDefault();
        filterPortionGuides();
    });

    const deleteModal = document.getElementById("portion-delete-modal");
    const deleteForm = document.getElementById("portion-delete-form");
    const deleteGuideTitle = document.getElementById("portion-delete-guide");
    const cancelDeleteButton = document.querySelector("[data-delete-cancel]");

    if (deleteModal && deleteForm && deleteGuideTitle && cancelDeleteButton) {
        let lastDeleteTrigger = null;

        resultsContainer.addEventListener("click", (event) => {
            const trigger = event.target.closest("[data-delete-trigger]");

            if (!trigger) {
                return;
            }

            lastDeleteTrigger = trigger;
            deleteForm.action = trigger.dataset.deleteUrl;
            deleteGuideTitle.textContent = trigger.dataset.guideTitle;
            deleteModal.showModal();
        });

        cancelDeleteButton.addEventListener("click", () => {
            deleteModal.close();
        });

        deleteModal.addEventListener("close", () => {
            if (lastDeleteTrigger && lastDeleteTrigger.isConnected) {
                lastDeleteTrigger.focus();
            }
        });

        deleteModal.addEventListener("click", (event) => {
            if (event.target === deleteModal) {
                deleteModal.close();
            }
        });
    }
});
