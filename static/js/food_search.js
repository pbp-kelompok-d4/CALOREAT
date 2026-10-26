(() => {
  const form = document.querySelector(".food-search");
  const input = document.querySelector(".food-search__input");
  if (!form || !input) return;

  const foods = [
    "Hamburger",
    "Indomie Goreng",
    "Greek Yogurt",
    "Oat Milk",
    "Chicken Breast",
    "Brown Rice",
    "Peanut Butter",
    "Banana",
    "Dark Chocolate",
    "Tofu",
    "Salmon",
    "Whole Wheat Bread",
  ];

  const pickRandomFood = () => {
    const candidates = foods.filter((item) => item !== input.placeholder);
    const nextFood = candidates[Math.floor(Math.random() * candidates.length)];
    input.placeholder = nextFood;
  };

  setInterval(() => {
    if (document.activeElement !== input && !input.value) {
      pickRandomFood();
    }
  }, 10000);

  form.addEventListener("submit", () => {
    if (!input.value.trim()) {
      input.value = input.placeholder;
    }
  });
})();
