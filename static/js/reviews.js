document.addEventListener("DOMContentLoaded", function () {
	const modal = document.getElementById("reviewModal");
	const openBtn = document.querySelector(".add-reviews-button");
	const closeBtn = document.getElementById("closeModalBtn");
	const cancelBtn = document.getElementById("cancelModalBtn");
	const form = document.getElementById("reviewForm");
	const modalTitle = modal.querySelector(".modal-header h3");
	const submitBtn = document.getElementById("submitBtn");
	const container = document.getElementById("reviewCardsContainer");
	const IS_AUTHORIZE = container.dataset.isAuthorized === "true";
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
							${IS_AUTHORIZE ? `<div class="review-card-actions">
								<button type="button" class="btn-update-review" data-id="${escapeHtml(review.id)}" aria-label="Edit review" title="Edit review">Edit</button>
								<button type="button" class="btn-delete-review" data-id="${escapeHtml(review.id)}" aria-label="Delete review" title="Delete review">
									<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
										<path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
										<path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/>
									</svg>
								</button>
							</div>` : ""}
						</div>
					</div>
				`;
			});

			container.innerHTML = htmlString;
		} catch (error) {
			console.error("Error:", error);
			container.innerHTML = `<div class="dashboard-review-empty"><p>Failed to load reviews.</p></div>`;
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
		form.dataset.url = form.dataset.addUrl;
		modalTitle.textContent = "Write a New Review";
		submitBtn.textContent = "Submit Review";
	}

	closeBtn.addEventListener("click", closeModal);
	cancelBtn.addEventListener("click", closeModal);

	window.addEventListener("click", (e) => {
		if (e.target === modal) closeModal();
	});

	// Add or edit a review
	form.addEventListener("submit", async function (e) {
		e.preventDefault();
		const formData = new FormData(form);

		try {
			const response = await fetch(form.dataset.url || form.dataset.addUrl, {
				method: "POST",
				body: formData,
			});

			if (response.redirected) {
				window.location.href = response.url;
				return;
			}

			if (response.ok) {
				closeModal();
				await refreshReviews();
			} else {
				const data = await response.json();
				alert(data.errors ? "Please check your review details." : "Failed to save the review.");
			}
		} catch (err) {
			console.error(err);
			alert("An error occurred.");
		}
	});
	
	// Helper to get CSRF token
	function getCookie(name) {
		let cookieValue = null;
		if (document.cookie && document.cookie !== '') {
			const cookies = document.cookie.split(';');
			for (let i = 0; i < cookies.length; i++) {
				const cookie = cookies[i].trim();
				if (cookie.substring(0, name.length + 1) === (name + '=')) {
					cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
					break;
				}
			}
		}
		return cookieValue;
	}

	// Edit or delete review via AJAX
	container.addEventListener("click", async (e) => {
		const editBtn = e.target.closest(".btn-update-review");
		if (editBtn) {
			const reviewId = editBtn.dataset.id;
			const review = (await fetch(container.dataset.url).then((response) => response.json()))
				.find((item) => item.id === reviewId);
			if (!review) {
				alert("Review not found.");
				return;
			}

			form.elements.customer_name.value = review.customer_name;
			form.elements.star.value = review.star;
			form.elements.content.value = review.content;
			form.dataset.url = form.dataset.editUrlTemplate.replace(
				"00000000-0000-0000-0000-000000000000",
				reviewId
			);
			modalTitle.textContent = "Edit Review";
			submitBtn.textContent = "Save Changes";
			modal.style.display = "flex";
			return;
		}

		const deleteBtn = e.target.closest(".btn-delete-review");
		if (!deleteBtn) return;

		const reviewId = deleteBtn.dataset.id;
		if (!reviewId) return;

		if (!confirm("Are you sure you want to delete this review?")) {
			return;
		}

		try {
			const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken') || '';
			const response = await fetch(`/reviews/delete-ajax/${reviewId}/`, {
				method: "POST",
				headers: {
					"X-CSRFToken": csrfToken,
				},
			});

			if (response.ok) {
				await refreshReviews();
			} else {
				alert("Failed to delete the review.");
			}
		} catch (err) {
			console.error("Error deleting review:", err);
			alert("An error occurred while deleting the review.");
		}
	});
});