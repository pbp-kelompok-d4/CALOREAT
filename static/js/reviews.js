document.addEventListener("DOMContentLoaded", function () {
	const modal = document.getElementById("reviewModal");
	const openBtn = document.querySelector(".add-reviews-button");
	const closeBtn = document.getElementById("closeModalBtn");
	const cancelBtn = document.getElementById("cancelModalBtn");
	const form = document.getElementById("reviewForm");
	const modalTitle = modal.querySelector(".modal-header h3");
	const submitBtn = document.getElementById("submitBtn");
	const container = document.getElementById("reviewCardsContainer");
	const loadMoreWrapper = document.getElementById("loadMoreReviewsWrapper");
	const loadMoreBtn = document.getElementById("loadMoreReviewsBtn");
	const starFiltersContainer = document.getElementById("reviewStarFilters");
	const starPicker = document.getElementById("starRatingPicker");
	const selectAllBtn = document.getElementById("selectAllReviewsBtn");
	const bulkDeleteBtn = document.getElementById("bulkDeleteReviewsBtn");
	const isSuperuser = container && container.dataset.isSuperuser === "true";
	let visibleReviewsCount = 6;
	const reviewsIncrement = 3;
	let selectedStar = "";
	let onlyMine = false;
	const selectedReviewIds = new Set();

	function countFilledStars(starString) {
		return (String(starString || "★★★★★").match(/★/g) || []).length || 5;
	}

	function renderStarPicker(count) {
		if (!starPicker) return;
		starPicker.querySelectorAll(".star-rating-btn").forEach((btn) => {
			const rating = Number(btn.dataset.rating);
			btn.classList.toggle("is-filled", rating <= count);
			btn.setAttribute("aria-checked", String(rating === count));
		});
	}

	function setStarRating(starValue) {
		const normalized = starValue || "★★★★★";
		if (form && form.elements.star) {
			form.elements.star.value = normalized;
		}
		renderStarPicker(countFilledStars(normalized));
	}

	if (starPicker) {
		starPicker.addEventListener("click", (e) => {
			const starBtn = e.target.closest(".star-rating-btn");
			if (!starBtn) return;
			setStarRating(starBtn.dataset.value);
		});

		starPicker.addEventListener("mouseover", (e) => {
			const starBtn = e.target.closest(".star-rating-btn");
			if (!starBtn) return;
			renderStarPicker(Number(starBtn.dataset.rating));
		});

		starPicker.addEventListener("mouseleave", () => {
			const currentVal = form && form.elements.star ? form.elements.star.value : "★★★★★";
			renderStarPicker(countFilledStars(currentVal));
		});
	}

	// XSS protection
	function escapeHtml(value) {
		return String(value ?? '')
			.replaceAll('&', '&amp;')
			.replaceAll('<', '&lt;')
			.replaceAll('>', '&gt;')
			.replaceAll('"', '&quot;')
			.replaceAll("'", '&#39;');
	}

	function buildReviewsUrl() {
		const url = new URL(container.dataset.url, window.location.origin);
		if (selectedStar) {
			url.searchParams.set("star", selectedStar);
		}
		if (onlyMine) {
			url.searchParams.set("mine", "1");
		}
		return url.toString();
	}

	function updateBulkDeleteUI() {
		if (!isSuperuser) return;
		const checkboxes = Array.from(container.querySelectorAll(".review-select-checkbox"));
		const visibleIds = checkboxes.map((cb) => cb.dataset.id);

		Array.from(selectedReviewIds).forEach((id) => {
			if (!visibleIds.includes(id)) {
				selectedReviewIds.delete(id);
			}
		});

		const allVisibleSelected = checkboxes.length > 0 && checkboxes.every((cb) => selectedReviewIds.has(cb.dataset.id));

		if (selectAllBtn) {
			selectAllBtn.style.display = checkboxes.length > 0 ? "inline-flex" : "none";
			selectAllBtn.textContent = allVisibleSelected ? "Deselect All" : "Select All";
		}

		if (bulkDeleteBtn) {
			bulkDeleteBtn.style.display = selectedReviewIds.size > 0 ? "inline-flex" : "none";
			bulkDeleteBtn.textContent = `Delete Selected (${selectedReviewIds.size})`;
		}
	}

    // get reviews
	async function refreshReviews() {
		try {
			const response = await fetch(buildReviewsUrl());
			const reviews = await response.json();

			// If 0 reviews
			if (reviews.length === 0) {
				let emptyMessage = "There are no reviews yet, add some!";
				if (onlyMine) {
					emptyMessage = "You haven't written a review yet.";
				} else if (selectedStar) {
					emptyMessage = "No reviews found for this star rating.";
				}
				container.innerHTML = `
					<div class="dashboard-review-empty">
						<p>${emptyMessage}</p>
					</div>
				`;
				if (loadMoreWrapper) {
					loadMoreWrapper.style.display = "none";
				}
				selectedReviewIds.clear();
				updateBulkDeleteUI();
				return;
			}

			// Render card for each review
			let htmlString = "";
			reviews.slice(0, visibleReviewsCount).forEach((review) => {
				const isSelected = selectedReviewIds.has(String(review.id));
				htmlString += `
					<div class="dashboard-review-card${isSelected ? " is-selected" : ""}">
						${isSuperuser ? `<input type="checkbox" class="review-select-checkbox" data-id="${escapeHtml(review.id)}" ${isSelected ? "checked" : ""} aria-label="Select review by ${escapeHtml(review.customer_name)}">` : ""}
						<img class="review-avatar" src="${escapeHtml(review.profile_picture)}" alt="${escapeHtml(review.customer_name)}'s profile picture" loading="lazy">
						<div class="review-details">
							<h3>${escapeHtml(review.customer_name)}</h3>
							<div class="review-stars">${escapeHtml(review.star)}</div>
							<div class="time">${escapeHtml(review.date)}</div>
							<p>${escapeHtml(review.content)}</p>
							${!isSuperuser && review.can_edit ? `<div class="review-card-actions">
								<button type="button" class="btn-update-review" data-id="${escapeHtml(review.id)}" aria-label="Edit review" title="Edit review">
									<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pencil" viewBox="0 0 16 16">
									<path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325"/>
									</svg>
								</button>
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

			if (loadMoreWrapper) {
				loadMoreWrapper.style.display = reviews.length > visibleReviewsCount ? "flex" : "none";
			}
			updateBulkDeleteUI();
		} catch (error) {
			console.error("Error:", error);
			container.innerHTML = `<div class="dashboard-review-empty"><p>Failed to load reviews.</p></div>`;
			if (loadMoreWrapper) {
				loadMoreWrapper.style.display = "none";
			}
		}
	}

	if (starFiltersContainer) {
		starFiltersContainer.addEventListener("click", (e) => {
			const filterBtn = e.target.closest(".review-filter-btn");
			if (!filterBtn) return;

			if (filterBtn.dataset.mine === "1") {
				onlyMine = true;
				selectedStar = "";
			} else {
				onlyMine = false;
				selectedStar = filterBtn.dataset.star || "";
			}
			visibleReviewsCount = 6;
			selectedReviewIds.clear();

			starFiltersContainer.querySelectorAll(".review-filter-btn").forEach((btn) => {
				btn.classList.toggle("active", btn === filterBtn);
			});

			refreshReviews();
		});
	}

	if (loadMoreBtn) {
		loadMoreBtn.addEventListener("click", () => {
			visibleReviewsCount += reviewsIncrement;
			refreshReviews();
		});
	}

	if (selectAllBtn) {
		selectAllBtn.addEventListener("click", () => {
			const checkboxes = Array.from(container.querySelectorAll(".review-select-checkbox"));
			const allSelected = checkboxes.length > 0 && checkboxes.every((cb) => cb.checked);
			checkboxes.forEach((cb) => {
				cb.checked = !allSelected;
				const card = cb.closest(".dashboard-review-card");
				if (!allSelected) {
					selectedReviewIds.add(cb.dataset.id);
					if (card) card.classList.add("is-selected");
				} else {
					selectedReviewIds.delete(cb.dataset.id);
					if (card) card.classList.remove("is-selected");
				}
			});
			updateBulkDeleteUI();
		});
	}

	if (bulkDeleteBtn) {
		bulkDeleteBtn.addEventListener("click", async () => {
			if (selectedReviewIds.size === 0) return;
			if (!confirm(`Are you sure you want to delete ${selectedReviewIds.size} selected review(s)?`)) {
				return;
			}

			try {
				const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken') || '';
				const response = await fetch(container.dataset.bulkDeleteUrl, {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
						"X-CSRFToken": csrfToken,
					},
					body: JSON.stringify({ ids: Array.from(selectedReviewIds) }),
				});

				if (response.redirected) {
					window.location.href = response.url;
					return;
				}

				if (response.ok) {
					selectedReviewIds.clear();
					await refreshReviews();
					showToast("Selected reviews deleted!", "success");
				} else {
					showToast("Failed to delete selected reviews.", "error");
				}
			} catch (err) {
				console.error("Error bulk deleting reviews:", err);
				showToast("An error occurred while deleting reviews.", "error");
			}
		});
	}

	// call every time page started
	refreshReviews();

	// Popup modal
	if (openBtn) {
		openBtn.addEventListener("click", () => {
			if (openBtn.dataset.authenticated !== "true") {
				window.location.href = openBtn.dataset.loginUrl;
				return;
			}
			setStarRating("★★★★★");
			modal.style.display = "flex";
		});
	}

	function closeModal() {
		modal.style.display = "none";
		form.reset();
		setStarRating("★★★★★");
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
		const isEdit = Boolean(form.dataset.url && form.dataset.url !== form.dataset.addUrl);

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
				showToast(isEdit ? "Review updated!" : "Review added!", "success");
			} else {
				const data = await response.json();
				showToast(
					data.message || (data.errors ? "Please check your review details." : "Failed to save the review."),
					"error"
				);
			}
		} catch (err) {
			console.error(err);
			showToast("An error occurred.", "error");
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

	container.addEventListener("change", (e) => {
		const checkbox = e.target.closest(".review-select-checkbox");
		if (!checkbox) return;
		const id = checkbox.dataset.id;
		const card = checkbox.closest(".dashboard-review-card");
		if (checkbox.checked) {
			selectedReviewIds.add(id);
			if (card) card.classList.add("is-selected");
		} else {
			selectedReviewIds.delete(id);
			if (card) card.classList.remove("is-selected");
		}
		updateBulkDeleteUI();
	});

	// Edit or delete review via AJAX
	container.addEventListener("click", async (e) => {
		const editBtn = e.target.closest(".btn-update-review");
		if (editBtn) {
			const reviewId = editBtn.dataset.id;
			const review = (await fetch(container.dataset.url).then((response) => response.json()))
				.find((item) => item.id === reviewId);
			if (!review) {
				showToast("Review not found.", "error");
				return;
			}

			form.elements.customer_name.value = review.customer_name;
			setStarRating(review.star);
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

			if (response.redirected) {
				window.location.href = response.url;
				return;
			}

			if (response.ok) {
				selectedReviewIds.delete(reviewId);
				await refreshReviews();
				showToast("Review deleted!", "success");
			} else {
				showToast("Failed to delete the review.", "error");
			}
		} catch (err) {
			console.error("Error deleting review:", err);
			showToast("An error occurred while deleting the review.", "error");
		}
	});
});
