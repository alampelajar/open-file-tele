# Telegram .open Userbot

Userbot Telegram berbasis Python 3.11 + Telethon. Balas pesan berisi dokumen `.txt` dengan `.open`; akun akan membalas informasi file dan preview maksimal 100 baris pertama.

## Persyaratan

- Windows 10/11
- Python 3.11
- Akun Telegram
- Telegram API ID dan API hash dari https://my.telegram.org

## Instalasi Windows

Clone repository:

```powershell
git clone https://github.com/alampelajar/open-file-tele.git
cd open-file-tele
```

Buat virtual environment dan instal dependensi:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Jika aktivasi PowerShell diblokir, buka CMD di folder proyek dan jalankan:

```bat
.venv\Scripts\activate.bat
```

## Konfigurasi

1. Buka https://my.telegram.org dan login.
2. Masuk ke **API development tools** dan salin API ID serta API hash.
3. Buat salinan `.env.example` dengan nama `.env`.
4. Isi `API_ID` dan `API_HASH` pada `.env`.

Jangan commit atau membagikan `.env` maupun file `*.session`: keduanya dapat memberikan akses sensitif ke akun.

## Jalankan

```powershell
python main.py
```

Saat pertama kali dijalankan, masukkan nomor telepon, kode login Telegram, dan password verifikasi dua langkah jika diminta. Session akan disimpan lokal agar login tidak perlu diulang setiap kali.

## Cara pakai

1. Pastikan program berjalan.
2. Di Telegram, buka pesan yang memiliki lampiran file `.txt`.
3. Reply/balas pesan file itu dan kirim `.open`.
4. Userbot membalas dengan nama file, ukuran, jumlah baris, dan preview 100 baris pertama.

## Batasan

- Hanya memproses file berakhiran `.txt`.
- Ukuran file maksimum 10 MB.
- Preview dibatasi hingga 100 baris.
- Program harus tetap berjalan agar command diproses.
- Gunakan hanya untuk file yang kamu miliki atau punya izin untuk membacanya.
