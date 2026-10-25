(function () {
  var dataEl = document.getElementById('foods-data');
  if (!dataEl) return;

  var FOODS = JSON.parse(dataEl.textContent);
  var NC = { A: '#2E8B3D', B: '#85BB2F', C: '#F2B705', D: '#EE8100', E: '#E63E11' };
  var dlg = document.getElementById('cat-dlg');

  // Buat elemen HTML dengan aman (teks tidak dibaca sebagai HTML)
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }
  function nilai(v) { return (v === null || v === undefined) ? '-' : v; }

  // Satu baris batang, contoh: Protein ====== 12 g
  function bar(label, v, color) {
    var box = el('div', 'cat-bar');
    var top = el('div');
    top.appendChild(el('span', '', label));
    top.appendChild(el('span', '', nilai(v) + (v === null ? '' : ' g')));
    var tr = el('div', 'cat-tr'), i = el('i');
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
    if (!list.length) box.appendChild(el('span', 'cat-tg', 'Belum ada data'));
    list.forEach(function (t) { box.appendChild(el('span', 'cat-tg', t)); });
    return box;
  }

  // Isi huruf Nutri-Score A-E di setiap kartu
  document.querySelectorAll('.cat-ns[data-grade]').forEach(function (n) {
    'ABCDE'.split('').forEach(function (x) {
      var b = el('b', x === n.dataset.grade ? 'on' : '', x);
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
    kiri.appendChild(el('h4', '', 'Makronutrisi'));
    kiri.appendChild(bar('Protein', f.protein, '#7BA05B'));
    kiri.appendChild(bar('Karbohidrat', f.karbo, '#F2B705'));
    kiri.appendChild(bar('Lemak', f.lemak, '#F07167'));
    kiri.appendChild(bar('Serat', f.serat, '#B7C98F'));
    kiri.appendChild(bar('Gula', f.gula, '#E8C46A'));

    var kanan = el('div');
    kanan.appendChild(el('h4', '', 'Vitamin'));
    kanan.appendChild(tags(f.vitamin));
    kanan.appendChild(el('h4', '', 'Mineral'));
    kanan.appendChild(tags(f.mineral));

    db.appendChild(kiri);
    db.appendChild(kanan);
    dlg.showModal();
  }

  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-i]');
    if (b) bukaDetail(+b.dataset.i);
    if (e.target.id === 'cat-cl' || e.target === dlg) dlg.close();
  });
})();