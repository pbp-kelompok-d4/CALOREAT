document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("reviewModal");
    const openBtn = document.querySelector(".add-reviews-button");
    const closeBtn = document.getElementById("closeModalBtn");
    const cancelBtn = document.getElementById("cancelModalBtn");
    const form = document.getElementById("reviewForm");
    const reviewComments = document.querySelector(".dashboard-review-comments");

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

    // Submit via AJAX
    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        const formData = new FormData(form);

        try {
            const response = await fetch(form.dataset.url, {
                method: "POST",
                body: formData,
            });

          const data = await response.json();

          if (response.ok) {
              const newCardHTML = `
                  <div class="dashboard-review-card">
                      <img class="review-avatar" src="${data.review.profile_picture}" alt="${data.review.customer_name}'s profile picture" loading="lazy">
                          <div class="review-details">
                              <h3>${data.review.customer_name}</h3>
                              <div class="review-stars">${data.review.star}</div>
                              <div class="time">${data.review.date}</div>
                              <p>${data.review.content}</p>
                      </div>
                  </div>
              `;
            
              const emptyMsg = document.querySelector(".dashboard-review-empty");
              if (emptyMsg) emptyMsg.remove();

              reviewComments.insertAdjacentHTML("afterbegin", newCardHTML);

              /* Remove card if more than set amount */
              const reviewCards = reviewComments.querySelectorAll(".dashboard-review-card");
              reviewCards.forEach((card, index) => {
                  if (index >= 6) {
                      card.remove();
                  }
              });
              closeModal();
          } else {
              alert("Gagal menambahkan review.");
          }
        } catch (err) {
            console.error(err);
            alert("Terjadi error!.");
        }
    });
});