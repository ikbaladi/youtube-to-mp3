# 🎵 YouTube to MP3 Downloader

Aplikasi web sederhana untuk download video YouTube dan convert ke MP3 256kbps.

## ✨ Fitur

- ✅ Download video tunggal
- ✅ Download playlist (pilih video yang diinginkan)
- ✅ Format MP3 256kbps
- ✅ UI sederhana dan mudah digunakan
- ✅ Progress bar real-time
- ✅ Download batch untuk playlist

## 🚀 Instalasi

### 1. Clone Repository
```bash
git clone <repo-url>
cd youtube-mp3-downloader
```

### 2. Install Dependencies
```bash
# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 3. Install FFmpeg
- **Windows:** Download dari [ffmpeg.org](https://ffmpeg.org/download.html)
- **Mac:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

### 4. Konfigurasi
Edit file `.env` sesuai kebutuhan (opsional)

### 5. Jalankan Aplikasi
```bash
python -m app.main
```

Buka browser: `http://localhost:8000`

## 📖 Cara Penggunaan

1. Paste URL YouTube (video atau playlist)
2. Klik "Cek Video"
3. Untuk playlist: pilih video yang ingin didownload
4. Klik "Download MP3"
5. Tunggu proses selesai
6. Download file

## 🛠️ Teknologi

- **Backend:** FastAPI + Python
- **Downloader:** yt-dlp
- **Converter:** FFmpeg
- **Frontend:** Vanilla JavaScript + CSS

## 📝 Catatan

- File otomatis terhapus setelah 1 jam
- Maximum file size: 100MB per video
- Concurrent downloads: 3 video

## 📄 License

MIT License