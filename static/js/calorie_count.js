(() => {
  const app = document.querySelector("#calorie-app");
  if (!app) return;

  const today = app.dataset.today;
  const defaultMeal = app.dataset.defaultMeal;
  let selectedDate = today;
  let searchPage = 1;
  let lastSearchQuery = "";
  let activeProduct = null;
  let toastTimer = null;
  let pendingUndo = null;

  const $ = (selector, root = document) => root.querySelector(selector);
  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  };
  const csrfToken = () => {
    const item = document.cookie.split(";").map((part) => part.trim()).find((part) => part.startsWith("csrftoken="));
    return item ? decodeURIComponent(item.slice("csrftoken=".length)) : "";
  };
  async function api(path, options = {}) {
    const method = options.method || "GET";
    const headers = { Accept: "application/json", ...(options.headers || {}) };
    if (options.body !== undefined) headers["Content-Type"] = "application/json";
    if (method !== "GET") headers["X-CSRFToken"] = csrfToken();
    const response = await fetch(path, { ...options, method, headers, credentials: "same-origin" });
    let data = {};
    try { data = await response.json(); } catch (_) { /* handled as a generic API error below */ }
    if (!response.ok) {
      const messages = {
        query_too_short: "Enter at least 2 characters to search.",
        slow_down: "One moment, then try again.",
        upstream_unavailable: "Open Food Facts is temporarily unavailable. You can add this food manually.",
        product_not_found: "No product found for that barcode.",
        future_date: "You cannot select a future date.",
      };
      const error = new Error(messages[data.error] || data.error || `Request failed (HTTP ${response.status}).`);
      error.code = data.error;
      error.status = response.status;
      throw error;
    }
    return data;
  }
  function busy(region, isBusy) { region.setAttribute("aria-busy", String(isBusy)); }
  function state(region, message, error = false) {
    const notice = el("div", `region-state${error ? " is-error" : ""}`);
    notice.append(el("p", "", message));
    if (error) {
      const retry = el("button", "region-retry", "Retry");
      retry.type = "button";
      notice.append(retry);
    }
    region.replaceChildren(notice);
  }
  function formatNumber(value, digits = 0) {
    if (value === null || value === undefined || value === "") return "—";
    return new Intl.NumberFormat(undefined, { maximumFractionDigits: digits }).format(Number(value));
  }
  function localDateLabel(iso) {
    const [year, month, day] = iso.split("-").map(Number);
    return new Intl.DateTimeFormat(undefined, { weekday: "short", day: "2-digit", month: "short", year: "numeric" }).format(new Date(year, month - 1, day));
  }
  function updateDateControls() {
    const time = $("#selected-date");
    time.dateTime = selectedDate;
    time.textContent = localDateLabel(selectedDate);
    $("#next-day").disabled = selectedDate >= today;
    $("#calories-title").textContent = selectedDate === today ? "Today's calories" : `Calories · ${localDateLabel(selectedDate)}`;
    $("#meals-title").textContent = selectedDate === today ? "Meals today" : `Meals · ${localDateLabel(selectedDate)}`;
  }
  const shiftDate = (iso, days) => {
    const [year, month, day] = iso.split("-").map(Number);
    const value = new Date(year, month - 1, day + days);
    return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}`;
  };

  async function loadSummary() {
    const region = $("#summary-region");
    busy(region, true);
    state($("#summary-content"), "Loading your summary…");
    try {
      const data = await api(`/api/summary/?date=${encodeURIComponent(selectedDate)}`);
      renderSummary(data);
    } catch (error) { state($("#summary-content"), `${error.message} Select to retry.`, true); }
    finally { busy(region, false); }
  }
  function renderSummary(data) {
    const region = $("#summary-content");
    const goal = data.goal_kcal;
    $("#goal-label").textContent = goal ? `Goal ${formatNumber(goal)} kcal` : "Set up your profile";
    const ring = el("div", "calorie-ring");
    const percent = goal ? Math.min((data.consumed_kcal / goal) * 100, 100) : 0;
    ring.style.setProperty("--ring-progress", `${percent}%`);
    ring.classList.toggle("is-over", Boolean(data.over_goal));
    ring.setAttribute("role", "img");
    ring.setAttribute("aria-label", `${formatNumber(data.consumed_kcal)} of ${goal ? formatNumber(goal) : "no"} kcal${data.remaining_kcal !== null ? `; ${formatNumber(data.remaining_kcal)} kcal remaining` : "; complete your profile to set a goal"}`);
    const ringText = el("div", "calorie-ring__text");
    ringText.append(el("strong", "", formatNumber(data.consumed_kcal)), el("span", "", goal ? `of ${formatNumber(goal)} kcal` : "kcal consumed"));
    ring.append(ringText);
    const bars = el("div", "nutrition-bars");
    ["carbs", "protein", "fat"].forEach((macro) => {
      const values = data.macros[macro];
      const row = el("div", "nutrition-bar");
      const line = el("div", "nutrition-bar__label");
      line.append(el("strong", "", macro[0].toUpperCase() + macro.slice(1)), el("span", "", `${formatNumber(values.consumed_g, 1)} / ${formatNumber(values.target_g, 1)} g`));
      const track = el("div", `nutrition-bar__track ${macro}`);
      const fill = el("span");
      fill.style.width = values.target_g ? `${Math.min(values.consumed_g / values.target_g * 100, 100)}%` : "0%";
      track.append(fill);
      row.append(line, track);
      bars.append(row);
    });
    const summaryItems = [ring, bars];
    if (!goal) {
      const note = el("p", "summary-profile-note", "Complete your profile to see calories remaining and macro targets.");
      summaryItems.push(note);
    } else {
      const remaining = el("p", `remaining-kcal${data.over_goal ? " is-over" : ""}`,
        data.over_goal ? `${formatNumber(Math.abs(data.remaining_kcal))} kcal over goal` : `${formatNumber(data.remaining_kcal)} kcal left today`);
      summaryItems.push(remaining);
    }
    region.replaceChildren(...summaryItems);
    $("#daily-status").textContent = data.remaining_kcal === null
      ? "Complete your profile to calculate your personal daily target."
      : data.over_goal ? `${formatNumber(Math.abs(data.remaining_kcal))} kcal over your daily goal.` : `You have ${formatNumber(data.remaining_kcal)} kcal left today. Nice and steady.`;
  }

  async function loadEntries() {
    const panel = $("#meals-region");
    busy(panel, true);
    state($("#meals-content"), "Loading your meals…");
    try { renderMeals(await api(`/api/entries/?date=${encodeURIComponent(selectedDate)}`)); }
    catch (error) { state($("#meals-content"), `${error.message} Select to retry.`, true); }
    finally { busy(panel, false); }
  }
  function renderMeals(data) {
    const content = $("#meals-content");
    const total = data.entries.reduce((sum, item) => sum + item.kcal, 0);
    $("#meals-total").textContent = `${formatNumber(total)} kcal`;
    const meals = ["breakfast", "lunch", "dinner", "snack"];
    const titles = { breakfast: "Breakfast", lunch: "Lunch", dinner: "Dinner", snack: "Snacks" };
    const nodes = [];
    for (const meal of meals) {
      const items = data.entries.filter((entry) => entry.meal === meal);
      const group = el("section", "meal-group");
      const header = el("div", "meal-group__heading");
      header.append(el("h3", "", titles[meal]), el("span", "", `${formatNumber(data.meal_totals[meal] || 0)} kcal`));
      group.append(header);
      if (!items.length) {
        const empty = el("button", "empty-meal-action", `+ Add ${meal === "snack" ? "snack" : meal}`);
        empty.type = "button";
        empty.addEventListener("click", () => { $("#food-search-input").focus(); window.scrollTo({ top: 0, behavior: "smooth" }); });
        group.append(empty);
      } else {
        for (const entry of items) group.append(renderEntry(entry));
      }
      nodes.push(group);
    }
    content.replaceChildren(...nodes);
  }
  function renderEntry(entry) {
    const row = el("article", "meal-entry");
    const main = el("div", "meal-entry__main");
    const info = el("div", "meal-entry__info");
    info.append(el("strong", "", entry.name));
    if (entry.brand) info.append(el("span", "meal-entry__brand", entry.brand));
    info.append(el("span", "meal-entry__amount", `${formatNumber(entry.grams, 1)} g`));
    main.append(info, el("strong", "meal-entry__kcal", `${formatNumber(entry.kcal)} kcal`));
    row.append(main);
    const actions = el("div", "meal-entry__actions");
    const edit = el("details", "entry-edit");
    const summary = el("summary", "", "Edit");
    const form = el("form", "entry-edit__form");
    form.innerHTML = `<label>Amount (g)<input name="grams" type="number" min="1" max="5000" step="1" value="${Number(entry.grams)}" required></label><label>Meal<select name="meal"><option value="breakfast">Breakfast</option><option value="lunch">Lunch</option><option value="dinner">Dinner</option><option value="snack">Snacks</option></select></label><button type="submit">Save</button>`;
    form.elements.meal.value = entry.meal;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const submit = form.querySelector("button[type='submit']");
      submit.disabled = true;
      try {
        await api(`/api/entries/${entry.id}/`, { method: "PATCH", body: JSON.stringify({ grams: form.elements.grams.value, meal: form.elements.meal.value }) });
        edit.open = false;
        await refreshDay();
        showToast("Food updated");
      } catch (error) { form.append(el("p", "form-error", error.message)); }
      finally { submit.disabled = false; }
    });
    edit.append(summary, form);
    const remove = el("button", "text-button is-danger", "Delete");
    remove.type = "button";
    remove.addEventListener("click", async () => {
      remove.disabled = true;
      try {
        const result = await api(`/api/entries/${entry.id}/`, { method: "DELETE" });
        await refreshDay();
        showToast(`${entry.name} deleted`, { kind: "restore", entry: result.entry });
      } catch (error) { showToast(error.message); }
      finally { remove.disabled = false; }
    });
    actions.append(edit, remove);
    row.append(actions);
    return row;
  }

  async function loadWeek() {
    const panel = $("#week-region");
    busy(panel, true);
    state($("#week-content"), "Loading your weekly summary…");
    try { renderWeek(await api(`/api/summary/week/?end=${encodeURIComponent(selectedDate)}`)); }
    catch (error) { state($("#week-content"), `${error.message} Select to retry.`, true); }
    finally { busy(panel, false); }
  }
  function renderWeek(data) {
    const region = $("#week-content");
    $("#week-goal").textContent = data.goal_kcal ? `Goal ${formatNumber(data.goal_kcal)}` : "Set up your profile";
    const chart = el("div", "week-chart");
    chart.setAttribute("role", "img");
    const max = Math.max(data.goal_kcal || 0, ...data.days.map((day) => day.kcal), 1) * 1.12;
    const goalLine = el("div", "week-chart__goal-line");
    goalLine.style.bottom = `${Math.min((data.goal_kcal || 0) / max * 100, 100)}%`;
    goalLine.style.display = data.goal_kcal ? "block" : "none";
    goalLine.setAttribute("aria-hidden", "true");
    chart.append(goalLine);
    const columns = el("div", "week-chart__columns");
    let within = 0;
    let sum = 0;
    data.days.forEach((day) => {
      const selected = day.date === selectedDate;
      if (data.goal_kcal && day.kcal <= data.goal_kcal) within += 1;
      sum += day.kcal;
      const column = el("div", "week-column");
      const barWrap = el("div", "week-column__bar-wrap");
      const bar = el("span", `week-column__bar${selected ? " is-selected" : data.goal_kcal && day.kcal > data.goal_kcal ? " is-over" : ""}`);
      bar.style.height = `${Math.max(day.kcal ? day.kcal / max * 100 : 1, 1)}%`;
      bar.title = `${localDateLabel(day.date)}: ${formatNumber(day.kcal)} kcal${day.goal_kcal ? `; goal ${formatNumber(day.goal_kcal)} kcal` : ""}`;
      bar.setAttribute("aria-hidden", "true");
      barWrap.append(bar);
      const dayName = new Intl.DateTimeFormat(undefined, { weekday: "short" }).format(new Date(`${day.date}T12:00:00`));
      column.append(barWrap, el("span", "week-column__day", dayName), el("span", "week-column__value", formatNumber(day.kcal)));
      column.setAttribute("aria-label", `${localDateLabel(day.date)}: ${formatNumber(day.kcal)} kcal${day.goal_kcal ? ` of ${formatNumber(day.goal_kcal)} kcal goal` : "; goal unavailable"}`);
      columns.append(column);
    });
    chart.setAttribute("aria-label", `Last seven days ending ${localDateLabel(data.end)}. ${data.days.map((day) => `${localDateLabel(day.date)} ${formatNumber(day.kcal)} kcal`).join("; ")}`);
    chart.append(columns);
    const average = Math.round(sum / data.days.length);
    const caption = el("p", "week-caption", `${formatNumber(average)} kcal daily average${data.goal_kcal ? ` · ${within} of 7 days within goal` : " · complete your profile to set a goal"}`);
    region.replaceChildren(chart, caption);
  }

  async function loadNeeds() {
    const panel = $("#needs-region");
    busy(panel, true);
    state($("#needs-content"), "Loading your profile…");
    try { renderNeeds(await api("/api/profile/")); }
    catch (error) { state($("#needs-content"), `${error.message} Select to retry.`, true); }
    finally { busy(panel, false); }
  }
  function renderNeeds(profile) {
    const region = $("#needs-content");
    if (!profile.complete) {
      const box = el("div", "needs-empty");
      box.append(el("p", "", "Complete your profile to calculate your daily needs."));
      const button = el("button", "button-primary needs-setup", "Set up profile");
      button.type = "button";
      button.addEventListener("click", () => openProfile(profile));
      box.append(button, el("p", "estimate-note", "Estimate, not medical advice."));
      region.replaceChildren(box);
      return;
    }
    const list = el("div", "needs-list");
    [["BMR", profile.bmr], ["Maintenance", profile.maintenance], ["Your goal", profile.goal_kcal]].forEach(([label, value]) => {
      const item = el("div", "needs-row");
      item.append(el("span", "", label), el("strong", "", `${formatNumber(value)} kcal`));
      list.append(item);
    });
    const edit = el("button", "needs-edit", "Edit profile");
    edit.type = "button";
    edit.addEventListener("click", () => openProfile(profile));
    const note = el("p", "estimate-note", "Estimate, not medical advice.");
    region.replaceChildren(list, edit, note);
  }

  async function refreshDay() { await Promise.all([loadSummary(), loadEntries(), loadWeek()]); }
  async function refreshPage() { updateDateControls(); await Promise.all([loadSummary(), loadEntries(), loadWeek(), loadNeeds()]); }
  $("#previous-day").addEventListener("click", () => { selectedDate = shiftDate(selectedDate, -1); refreshPage(); });
  $("#next-day").addEventListener("click", () => {
    if (selectedDate < today) { selectedDate = shiftDate(selectedDate, 1); refreshPage(); }
  });
  $("#summary-region").addEventListener("click", (event) => { if (event.target.closest(".region-state")) loadSummary(); });
  $("#meals-region").addEventListener("click", (event) => { if (event.target.closest(".region-state")) loadEntries(); });
  $("#week-region").addEventListener("click", (event) => { if (event.target.closest(".region-state")) loadWeek(); });
  $("#needs-region").addEventListener("click", (event) => { if (event.target.closest(".region-state")) loadNeeds(); });

  function setProductAmount(product, input, output) {
    const value = Math.max(1, Math.min(5000, Number(input.value) || 1));
    input.value = String(value);
    output.textContent = product.kcal_100g === null ? "— kcal" : `${formatNumber(product.kcal_100g * value / 100, 1)} kcal`;
  }
  function mealSelector(selected) {
    const select = el("select", "product-add__meal");
    select.setAttribute("aria-label", "Meal");
    [["breakfast", "Breakfast"], ["lunch", "Lunch"], ["dinner", "Dinner"], ["snack", "Snacks"]].forEach(([value, label]) => {
      const option = el("option", "", label); option.value = value; select.append(option);
    });
    select.value = selected || defaultMeal;
    return select;
  }
  function renderProduct(product) {
    const card = el("article", `food-result${product.has_nutrition ? "" : " is-missing"}`);
    const image = product.image ? el("img", "food-result__image") : el("span", "food-result__placeholder", "✧");
    if (product.image) { image.src = product.image; image.alt = ""; image.loading = "lazy"; }
    else image.setAttribute("aria-hidden", "true");
    const description = el("div", "food-result__description");
    description.append(el("p", "food-result__name", product.name));
    if (product.brand) description.append(el("p", "food-result__brand", product.brand));
    const meta = el("div", "food-result__meta");
    meta.append(el("span", "", product.has_nutrition ? `${formatNumber(product.kcal_100g, 1)} kcal / 100 g` : "No nutrition data"));
    if (product.nutriscore) {
      const score = el("span", "food-result__score", product.nutriscore.toUpperCase());
      score.dataset.score = product.nutriscore;
      score.setAttribute("aria-label", `Nutri-Score ${product.nutriscore.toUpperCase()}`);
      meta.append(score);
    }
    card.append(image, description, meta);
    if (!product.has_nutrition) {
      const manual = el("button", "manual-add-button", "Add manually");
      manual.type = "button";
      manual.addEventListener("click", () => openManual(product));
      card.append(manual);
      return card;
    }
    const add = el("div", "product-add");
    const amountLabel = el("label", "product-add__amount");
    amountLabel.append(el("span", "sr-only", "Amount in grams"));
    const amount = el("input"); amount.type = "number"; amount.min = "1"; amount.max = "5000"; amount.step = "1"; amount.value = String(Math.round(product.serving_g || 100)); amount.setAttribute("aria-label", "Amount in grams");
    const minus = el("button", "stepper-button", "−"); minus.type = "button"; minus.setAttribute("aria-label", "Decrease amount by 1 gram");
    const plus = el("button", "stepper-button", "+"); plus.type = "button"; plus.setAttribute("aria-label", "Increase amount by 1 gram");
    const meal = mealSelector(defaultMeal);
    const kcal = el("strong", "product-add__total");
    const submit = el("button", "button-primary product-add__submit", "Add"); submit.type = "button";
    const sync = () => setProductAmount(product, amount, kcal);
    amount.addEventListener("input", sync);
    minus.addEventListener("click", () => { amount.value = String(Math.max(1, Number(amount.value) - 1)); sync(); });
    plus.addEventListener("click", () => { amount.value = String(Math.min(5000, Number(amount.value) + 1)); sync(); });
    sync();
    amountLabel.append(minus, amount, plus);
    submit.addEventListener("click", async () => {
      submit.disabled = true;
      try {
        const payload = productPayload(product, Number(amount.value), meal.value);
        const result = await api("/api/entries/", { method: "POST", body: JSON.stringify(payload) });
        await refreshDay();
        showToast(`${product.name} added`, { kind: "delete", entry: result.entry });
        card.classList.add("is-added");
        submit.textContent = "Added";
      } catch (error) { showSearchError(error.message); }
      finally { submit.disabled = false; }
    });
    add.append(amountLabel, kcal, meal, submit);
    card.append(add);
    return card;
  }
  function productPayload(product, grams, meal) {
    return {
      date: selectedDate, meal, grams,
      name: product.name, brand: product.brand || "", off_code: product.code || "",
      kcal_100g: product.kcal_100g,
      protein_100g: product.protein_100g,
      carbs_100g: product.carbs_100g,
      fat_100g: product.fat_100g,
      nutriscore: product.nutriscore || "",
    };
  }
  function showSearchError(message) {
    const results = $("#food-search-results");
    const p = el("p", "region-state is-error", message);
    results.replaceChildren(p);
  }
  function renderSearchResults(data) {
    const region = $("#food-search-results");
    if (!data.results || !data.results.length) {
      state(region, "No matching products found. Try another name or add your food manually.");
      return;
    }
    region.replaceChildren(...data.results.map(renderProduct));
    const pagination = el("div", "search-pagination");
    const previous = el("button", "button-secondary", "Previous"); previous.type = "button"; previous.disabled = searchPage <= 1;
    const pageText = el("span", "", `Page ${searchPage}`);
    const next = el("button", "button-secondary", "Next"); next.type = "button"; next.disabled = data.results.length < 10;
    previous.addEventListener("click", () => runSearch(lastSearchQuery, searchPage - 1));
    next.addEventListener("click", () => runSearch(lastSearchQuery, searchPage + 1));
    pagination.append(previous, pageText, next);
    region.append(pagination);
  }
  async function runSearch(query, page = 1) {
    const submit = $("#food-search-form button[type='submit']");
    const region = $("#food-search-results");
    const barcode = /^\d{8,14}$/.test(query);
    if (!barcode && query.length < 2) { showSearchError("Enter at least 2 characters to search."); return; }
    lastSearchQuery = query; searchPage = page; submit.disabled = true; busy(region, true); state(region, "Searching Open Food Facts…");
    try {
      if (barcode) {
        const data = await api(`/api/foods/barcode/${encodeURIComponent(query)}/`);
        renderSearchResults({ results: [data.result] });
      } else {
        const data = await api(`/api/foods/search/?q=${encodeURIComponent(query)}&page=${page}`);
        renderSearchResults(data);
      }
    } catch (error) { showSearchError(error.message); }
    finally { submit.disabled = false; busy(region, false); }
  }
  $("#food-search-form").addEventListener("submit", (event) => {
    event.preventDefault();
    runSearch($("#food-search-input").value.trim(), 1);
  });

  function openProfile(profile = {}) {
    const form = $("#profile-form");
    ["sex", "birth_date", "height_cm", "weight_kg", "activity_level", "goal"].forEach((key) => { form.elements[key].value = profile[key] ?? ""; });
    $("#profile-error").hidden = true;
    $("#profile-dialog").showModal();
  }
  $("#nav-profile-setup")?.addEventListener("click", async () => {
    $("#nav-profile-setup").closest("details").open = false;
    try { openProfile(await api("/api/profile/")); }
    catch (error) { showToast(`Could not load your profile: ${error.message}`); }
  });
  $("#profile-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const submit = form.querySelector("button[type='submit']");
    const errorBox = $("#profile-error"); submit.disabled = true; errorBox.hidden = true;
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      const profile = await api("/api/profile/", { method: "PUT", body: JSON.stringify(data) });
      $("#profile-dialog").close();
      renderNeeds(profile); await refreshDay();
    } catch (error) { errorBox.textContent = error.message; errorBox.hidden = false; }
    finally { submit.disabled = false; }
  });
  $("#manual-entry-launch").addEventListener("click", () => openManual());
  function openManual(product = {}) {
    const form = $("#manual-form");
    form.elements.name.value = product.name || "";
    form.elements.brand.value = product.brand || "";
    form.elements.off_code.value = product.code || "";
    form.elements.nutriscore.value = product.nutriscore || "";
    form.elements.grams.value = Math.round(product.serving_g || 100);
    form.elements.kcal_100g.value = "";
    form.elements.protein_100g.value = product.protein_100g ?? "";
    form.elements.carbs_100g.value = product.carbs_100g ?? "";
    form.elements.fat_100g.value = product.fat_100g ?? "";
    form.elements.meal.value = defaultMeal;
    $("#manual-error").hidden = true;
    $("#manual-dialog").showModal();
  }
  $("#manual-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const submit = form.querySelector("button[type='submit']");
    const errorBox = $("#manual-error"); submit.disabled = true; errorBox.hidden = true;
    const data = Object.fromEntries(new FormData(form).entries());
    data.date = selectedDate;
    for (const key of ["grams", "kcal_100g", "protein_100g", "carbs_100g", "fat_100g"]) data[key] = data[key] === "" ? null : Number(data[key]);
    try {
      const result = await api("/api/entries/", { method: "POST", body: JSON.stringify(data) });
      $("#manual-dialog").close(); await refreshDay();
      showToast(`${data.name} added`, { kind: "delete", entry: result.entry });
    } catch (error) { errorBox.textContent = error.message; errorBox.hidden = false; }
    finally { submit.disabled = false; }
  });
  document.querySelectorAll("[data-close-dialog]").forEach((button) => button.addEventListener("click", () => button.closest("dialog").close()));

  function showToast(message, undo) {
    pendingUndo = undo || null;
    $("#undo-message").textContent = message;
    $("#undo-action").hidden = !pendingUndo;
    const toast = $("#undo-toast"); toast.hidden = false;
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => { toast.hidden = true; pendingUndo = null; }, 5000);
  }
  $("#undo-action").addEventListener("click", async () => {
    if (!pendingUndo) return;
    const action = pendingUndo;
    pendingUndo = null;
    window.clearTimeout(toastTimer);
    $("#undo-toast").hidden = true;
    try {
      if (action.kind === "delete") await api(`/api/entries/${action.entry.id}/`, { method: "DELETE" });
      if (action.kind === "restore") await api("/api/entries/", { method: "POST", body: JSON.stringify(action.entry) });
      await refreshDay();
      showToast("Change undone");
    } catch (error) { showToast(`Undo failed: ${error.message}`); }
  });
  updateDateControls();
  refreshPage();
})();
