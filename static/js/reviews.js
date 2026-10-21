document.addEventListener("DOMContentLoaded", function () {
	const modal = document.getElementById("reviewModal");
	const openBtn = document.querySelector(".add-reviews-button");
	const closeBtn = document.getElementById("closeModalBtn");
	const cancelBtn = document.getElementById("cancelModalBtn");
	const form = document.getElementById("reviewForm");
	const container = document.getElementById("reviewCardsContainer");
	const maxReviewsShown = 6;

	// XSS protection
	function escapeHtml(value) {
		return String(value ?? '')
			.replaceAll('&', '&amp;')
			.replaceAll('<', '&lt;')
			.replaceAll('>', '&gt;')
			.replaceAll('"', '&quot;')
			.replaceAll("'", '&#39;');
	}

    // get reviews
	async function refreshReviews() {
		try {
			const response = await fetch(container.dataset.url);
			const reviews = await response.json();

			// If 0 reviews
			if (reviews.length === 0) {
				container.innerHTML = `
					<div class="dashboard-review-empty">
						<p>There are no reviews yet, add some!</p>
					</div>
				`;
				return;
			}

			// Render card for each review
			let htmlString = "";
			reviews.slice(0, maxReviewsShown).forEach((review) => {
				htmlString += `
					<div class="dashboard-review-card">
						<img class="review-avatar" src="${escapeHtml(review.profile_picture)}" alt="${escapeHtml(review.customer_name)}'s profile picture" loading="lazy">
						<div class="review-details">
							<h3>${escapeHtml(review.customer_name)}</h3>
							<div class="review-stars">${escapeHtml(review.star)}</div>
							<div class="time">${escapeHtml(review.date)}</div>
							<p>${escapeHtml(review.content)}</p>
						</div>
					</div>
				`;
			});

			container.innerHTML = htmlString;
		} catch (error) {
			console.error("Error:", error);
			container.innerHTML = `<div class="dashboard-review-empty"><p>Gagal memuat review.</p></div>`;
		}
	}

	// call every time page started
	refreshReviews();

	// Popup modal
	openBtn.addEventListener("click", () => {
		modal.style.display = "flex";
	});

	function closeModal() {
		modal.style.display = "none";
		form.reset();
	}

	closeBtn.addEventListener("click", closeModal);
	cancelBtn.addEventListener("click", closeModal);

	window.addEventListener("click", (e) => {
		if (e.target === modal) closeModal();
	});

	// Add new review
	form.addEventListener("submit", async function (e) {
		e.preventDefault();
		const formData = new FormData(form);

		try {
			const response = await fetch(form.dataset.url, {
				method: "POST",
				body: formData,
			});

			if (response.ok) {
				closeModal();
				// asynchronous load
				await refreshReviews();
			} else {
				alert("Gagal menambahkan review.");
			}
		} catch (err) {
			console.error(err);
			alert("Terjadi error.");
		}
	});
});