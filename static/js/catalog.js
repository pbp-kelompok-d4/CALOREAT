(function () {
  var dataEl = document.getElementById('foods-data');
  if (!dataEl) return;

  var FOODS = JSON.parse(dataEl.textContent);
  var NC = { A: '#2E8B3D', B: '#85BB2F', C: '#F2B705', D: '#EE8100', E: '#E63E11' };
  var dlg = document.getElementById('cat-dlg');
  var closeButton = document.getElementById('cat-cl');
  var utilityClasses = {
    'cat-bar': 'mb-[10px] w-full text-[13px]',
    'cat-bar__top': 'mb-[3px] flex w-full min-w-0 items-center justify-between gap-3',
    'cat-tr': 'h-[7px] w-full overflow-hidden rounded bg-[var(--c-track)]',
    'cat-tr__fill': 'block h-[7px] rounded-[4px]',
    'cat-tags': 'mb-[14px] flex flex-wrap gap-[6px]',
    'cat-tag': 'rounded-full bg-[var(--c-chip)] px-[11px] py-[3px] text-[13px]',
    'cat-ns-grade': 'w-[14px] shrink-0 text-center font-normal text-white opacity-[0.35]',
    'cat-ns-grade-active': 'w-5 shrink-0 text-center font-bold text-white opacity-100',
    'cat-detail-title': 'mb-2 text-sm text-[var(--c-mute)]',
    'cat-detail-value': 'text-[var(--c-ink)]',
    'cat-detail-number': 'shrink-0 text-right text-[var(--c-ink)]'
  };

  // Buat elemen HTML dengan aman (teks tidak dibaca sebagai HTML)
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) {
      var utilities = cls.split(/\s+/).map(function (name) { return utilityClasses[name] || ''; }).filter(Boolean);
      e.className = [cls].concat(utilities).join(' ');
    }
    if (text !== undefined) e.textContent = text;
    return e;
  }
  function nilai(v) { return (v === null || v === undefined) ? '-' : v; }

  // Satu baris batang, contoh: Protein ====== 12 g
  function bar(label, v, color) {
    var box = el('div', 'cat-bar');
    var top = el('div', 'cat-bar__top');
    top.appendChild(el('span', 'cat-detail-value', label));
    top.appendChild(el('span', 'cat-detail-number', nilai(v) + (v === null ? '' : ' g')));
    var tr = el('div', 'cat-tr'), i = el('i', 'cat-tr__fill');
    i.style.width = Math.min(100, (v || 0) / 50 * 100) + '%';
    i.style.background = color;
    tr.appendChild(i);
    box.appendChild(top);
    box.appendChild(tr);
    return box;
  }

  // Daftar vitamin atau mineral dalam bentuk label kecil
  function tags(list) {
    var box = el('div', 'cat-tags');
    if (!list.length) box.appendChild(el('span', 'cat-tag', 'Belum ada data'));
    list.forEach(function (t) { box.appendChild(el('span', 'cat-tag', t)); });
    return box;
  }

  // Isi huruf Nutri-Score A-E di setiap kartu
  document.querySelectorAll('.cat-ns[data-grade]').forEach(function (n) {
    'ABCDE'.split('').forEach(function (x) {
      var b = el('b', x === n.dataset.grade ? 'cat-ns-grade-active' : 'cat-ns-grade', x);
      b.style.background = NC[x];
      n.appendChild(b);
    });
  });

  // Buka jendela detail untuk makanan ke-i
  function bukaDetail(i) {
    var f = FOODS[i];
    document.getElementById('cat-dt').textContent = f.nama;
    document.getElementById('cat-ds').textContent = nilai(f.kcal) + ' kcal per 100 g';
    var db = document.getElementById('cat-db');
    db.textContent = '';

    var kiri = el('div');
    kiri.appendChild(el('h4', 'cat-detail-title', 'Makronutrisi'));
    kiri.appendChild(bar('Protein', f.protein, '#7BA05B'));
    kiri.appendChild(bar('Karbohidrat', f.karbo, '#F2B705'));
    kiri.appendChild(bar('Lemak', f.lemak, '#F07167'));
    kiri.appendChild(bar('Serat', f.serat, '#B7C98F'));
    kiri.appendChild(bar('Gula', f.gula, '#E8C46A'));

    var kanan = el('div');
    kanan.appendChild(el('h4', 'cat-detail-title', 'Vitamin'));
    kanan.appendChild(tags(f.vitamin));
    kanan.appendChild(el('h4', 'cat-detail-title', 'Mineral'));
    kanan.appendChild(tags(f.mineral));

    db.appendChild(kiri);
    db.appendChild(kanan);
    closeButton.classList.remove('is-pointer-focused');
    dlg.showModal();
  }

  dlg.addEventListener('pointerdown', function (e) {
    if (e.target.closest('.cat-x') === closeButton) closeButton.classList.add('is-pointer-focused');
  });
  dlg.addEventListener('keydown', function (e) {
    if (e.key === 'Tab') closeButton.classList.remove('is-pointer-focused');
  });

  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-i]');
    if (b) bukaDetail(+b.dataset.i);
    if (e.target.id === 'cat-cl' || e.target === dlg) dlg.close();
  });
})();
