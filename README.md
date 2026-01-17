# Brutalist GitHub Stats Dashboard (rans0.github.io)

Sebuah dashboard personal dengan estetika **Brutalist Ink Splatter** yang menampilkan statistik GitHub secara real-time dan otomatis. Dashboard ini dirancang untuk memberikan visualisasi performa developer secara dinamis dan modern.

## 🚀 Fitur Utama

- **Modular Architecture**: Menggunakan sistem *dynamic section loader* untuk memisahkan komponen HTML (Header, Hero, Stats, Social, dll) agar mudah dikelola.
- **Fully Automated Stats**: Statistik diperbarui secara otomatis setiap hari menggunakan GitHub Actions dan Python.
- **Dynamic Activity Flow**: Grafik batang mingguan yang berubah tingginya sesuai dengan jumlah commit asli dalam 7 hari terakhir.
- **Responsive Design**: Tampilan yang optimal baik di desktop maupun perangkat mobile dengan sentuhan animasi brutalist.

## 📊 Data & Otomatisasi

Seluruh angka dan grafik pada dashboard ini ditarik langsung dari GitHub GraphQL API menggunakan script Python (`scripts/update_stats.py`).

| Data | Deskripsi | Logika Otomatisasi |
| :--- | :--- | :--- |
| **Total Commits** | Jumlah seluruh commit seumur hidup profil. | Diambil dari `totalCommitContributions`. |
| **Current Streak** | Jumlah hari berturut-turut melakukan commit. | Dihitung dari kalender kontribusi 365 hari terakhir. |
| **Total Repos** | Jumlah repository yang dimiliki. | Diambil dari `repositories.totalCount`. |
| **Stars & PRs** | Akumulasi bintang dan Pull Requests. | Penjumlahan otomatis dari seluruh metadata repo. |
| **Activity Flow** | Grafik batang Senin - Minggu. | Menampilkan tren commit 7 hari terakhir secara proporsional. |
| **Lines Committed** | Estimasi volume kode yang dikerjakan. | Dihitung berdasarkan formula: `(Disk Usage KB * 40) + (Commits * 100)`. |
| **AVG Monthly** | Rata-rata kontribusi bulanan. | Total kontribusi tahunan dibagi 12. |

## 🛠 Teknologi yang Digunakan

- **Frontend**: HTML5, Vanilla CSS (Brutalist Style), Tailwind CSS.
- **Automation**: Python 3.x, GitHub Actions (Workflow).
- **API**: GitHub GraphQL API v4.
- **Hosting**: GitHub Pages.

## ⚙️ Cara Menjalankan Secara Lokal

Karena proyek ini menggunakan fitur `fetch` untuk memuat modul HTML, Anda tidak bisa sekadar membuka file `index.html`. Anda harus menggunakan web server lokal:

```bash
# Menggunakan Python
python3 -m http.server 8000
```
Lalu buka `localhost:8000` di browser Anda.

## 🤖 Menyiapkan Otomatisasi (GitHub Actions)

Untuk mengaktifkan pembaruan otomatis setiap jam 12 malam (WIB):

1. Buat **Personal Access Token (PAT)** di akun GitHub Anda dengan scope `repo` dan `user`.
2. Masuk ke **Settings** repository > **Secrets and variables** > **Actions**.
3. Tambahkan **New repository secret** dengan nama `GH_TOKEN` dan isi dengan token PAT Anda.
4. Pastikan **Settings** > **Pages** > **Build and deployment** > Source diatur ke **"GitHub Actions"**.

---
*Built with code, logic, and a bit of chaos.* ✨
