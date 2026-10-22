# Anggota Kelompok
2506584893 - Andranu Dhawy Purditya

2506592125 - Nathanael Orrick Hatmoko

2506612814 - Samuel Haganta Surbakti

2506618881 - Muhammad Fachri Novelino

2506656936 - Kusuma Putra Abdillah Adhimaya

# Deskripsi Website:
CALOREAT adalah platform kalkulator dan pemantau nutrisi harian yang membantu pengguna menghitung calorie intake secara presisi sekaligus memahami kandungan gizi pada makanan. Mengusung prinsip Sustainable Living, CALOREAT tidak hanya berfokus pada target kesehatan personal pengguna, tetapi juga mengedukasi dampak emisi karbon (carbon footprint) dari pilihan makanan harian agar pengguna dapat mengambil keputusan konsumsi yang lebih bijak dan ramah lingkungan.

Tak hanya sekadar pelacak kalori, CALOREAT menyediakan panduan takaran porsi makan yang ideal untuk memenuhi kebutuhan gizi tanpa memicu pembelian berlebih. Melalui integrasi katalog nutrisi, panduan porsi harian, dan rekomendasi cegah sampah (zero-waste tips), CALOREAT memudahkan pengguna menjaga berat badan ideal sekaligus berkontribusi aktif dalam mengurangi food waste, menciptakan ekosistem gaya hidup sehat yang berkelanjutan bagi tubuh dan bumi.

# Public API
Public API yang kami gunakan bersumber dari basis data Open Food Facts: [https://id.openfoodfacts.org/]


# Daftar Modul

- Halaman Autentikasi, Profil dan Admin Portal: Halaman login, register, profil pengguna, dan admin portal untuk mengelola pengguna serta basis data makanan. (Samuel Haganta Surbakti)

- Homepage: Halaman utama yang menampilkan fitur-fitur unggulan website, edukasi singkat pola makan sehat, dan navigasi cepat. (Andranu Dhawy Purditya)

- About: Menyajikan informasi mengenai latar belakang, serta visi dan misi platform CALOREAT dalam mendukung pemenuhan gizi seimbang dan gaya hidup sehat. (Andranu Dhawy Purditya)

- Kalkulator & Pelacak Kalori: Pengguna dapat menghitung kebutuhan kalori harian (BMR/TDEE) serta mencatat asupan makanan harian secara teratur. (Nathanael Orrick Hatmoko)

- Katalog Nutrisi Makanan: Menyajikan daftar bahan dan menu makanan beserta detail informasi kandungan gizi sehat seperti makronutrisi (protein, karbohidrat, lemak) dan mikronutrisi (vitamin, mineral). (Muhammad Fachri Novelino)

- Panduan Porsi Makan Sehat: Menyajikan panduan takaran dan ukuran porsi makanan yang ideal untuk dikonsumsi harian sesuai kebutuhan gizi pengguna. (Kusuma Putra Abdillah Adhimaya)


# Role Pengguna

- Belum login: Dapat melihat halaman homepage, berita edukasi, dan profile page dengan akses terbatas

- login sebagai pengguna: Dapat mengakses kalkulator kalori, melengkapi profil, mengakses katalog nutrisi, dan panduan porsi makan sehat.

- login sebagai admin: Dapat merubah/menambahkan informasi pada katalog nutrisi dan panduan makan sehat, serta mengakses admin portal

# Tautan Figma

Link Figma : https://www.figma.com/design/V68iKwXFe8rn1on5zE9wi6/Caloreat?node-id=0-1&t=RW25UIKrE2cFGLEP-1





## Calorie Count

The authenticated `/calorie-count/` page supports food search and barcode lookup through a server-side Open Food Facts client, personal calorie targets, daily meal entries, and a seven-day summary. Data is isolated by account.

The JSON API is available at `/api/foods/search/`, `/api/foods/barcode/<code>/`, `/api/entries/`, `/api/entries/<id>/`, `/api/summary/`, `/api/summary/week/`, and `/api/profile/`. Mutating requests use the session cookie and Django CSRF token. Open Food Facts search responses are cached for 24 hours, and requests are throttled to stay within its search limits. The lookup credits [Open Food Facts](https://id.openfoodfacts.org/) under the ODbL.

After updating, apply the database migration with `python manage.py migrate`. To use a non-default contact for the Open Food Facts User-Agent, update `USER_AGENT` in `main/off.py` before deployment.
