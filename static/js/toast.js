class ToastManager {
	constructor() {
		this.container = null;
	}

	ensureContainer() {
		if (!this.container || !document.body.contains(this.container)) {
			this.container = document.createElement("div");
			this.container.className = "review-toast-container";
			this.container.setAttribute("aria-live", "polite");
			document.body.appendChild(this.container);
		}
		return this.container;
	}

	show(message, type = "success") {
		const container = this.ensureContainer();
		const toast = document.createElement("div");
		toast.className = `review-toast review-toast--${type}`;
		toast.textContent = message;
		container.appendChild(toast);

		window.setTimeout(() => {
			toast.style.opacity = "0";
			toast.style.transform = "translateY(8px)";
			window.setTimeout(() => {
				toast.remove();
			}, 200);
		}, 2600);
	}
}

const toastManager = new ToastManager();

function showToast(message, type = "success") {
	toastManager.show(message, type);
}

window.ToastManager = ToastManager;
window.showToast = showToast;
