# Daftar Layanan Hosting Gratis (Tanpa Kartu Kredit / Tanpa Visa)

Berikut adalah platform gratis yang bisa Anda gunakan untuk mendeploy aplikasi ini tanpa diminta kartu kredit/visa:

1. **Railway.app** (Direkomendasikan)
   - **Kelebihan:** Sangat mudah, mendukung Python, FastAPI, dan PostgreSQL/SQLite dengan cepat. Cukup login pakai akun GitHub.
   - **Cara Deploy:**
     1. Masuk ke [railway.app](https://railway.app/) menggunakan akun GitHub.
     2. Klik **New Project** → **Deploy from GitHub repo**.
     3. Pilih repository proyek ini, lalu Railway akan otomatis mendeteksi dan mendeploy aplikasi Anda.

2. **Koyeb.com**
   - **Kelebihan:** Menyediakan *Free Tier* server berbasis container tanpa perlu kartu kredit.
   - **Cara Deploy:**
     1. Buat akun di [koyeb.com](https://www.koyeb.com/).
     2. Buat App baru, hubungkan GitHub repository.
     3. Build command: `pip install -r requirements.txt` dan Run command: `python run_server.py`.

3. **Fly.io**
   - **Kelebihan:** Cepat dan handal (perlu install CLI Fly untuk setup awal, tidak meminta kartu kredit untuk tier gratis).
