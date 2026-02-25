# CIT-autograd

CIT-autograd adalah tool otomatis untuk menilai jawaban mahasiswa berbasis PDF atau image menggunakan answer key dan sistem penilaian terstruktur.

---

## Requirements

Pastikan Python sudah terinstall (disarankan Python 3.9+).

Install module yang dibutuhkan:

```bash
pip install PyMuPDF openai pandas openpyxl
```
---
## Project Structure (Example)
```bash
CIT-autograd/
│
├── autograd.py
├── student-answer/
│   └── Jawaban_Mahasiswa_Sosial_Theory.pdf
├── key-answer/
│   └── Kunci Jawaban Tugas Social Theory.pdf
```
## Usage

Jalankan melalui Command Prompt / Terminal dari direktori root project.

### First Run (Belum Pernah Ekstrak Kunci Jawaban)

Gunakan opsi --key_answer saat pertama kali menjalankan program.
```bash
python autograd.py --student_answer "alamat_file_jawaban_siswa.pdf" --key_answer "alamat_file_kunci_jawaban.pdf"
```
Contoh:
```bash
python autograd.py --student_answer "student-answer\Jawaban_Mahasiswa_Sosial_Theory.pdf" --key_answer "key-answer\Kunci Jawaban Tugas Social Theory.pdf"
```
### Run Berikutnya (Kunci Jawaban Sudah Diekstrak)

Jika kunci jawaban sudah pernah diekstrak, cukup jalankan:
```bash
python autograd.py --student_answer "alamat_file_jawaban_siswa.pdf"
```
Contoh:
```bash
python autograd.py --student_answer "student-answer\Jawaban_Mahasiswa_Sosial_Theory.pdf"
```
### Output
Program akan:
- Mengekstrak teks dari file PDF
- Membandingkan jawaban mahasiswa dengan kunci jawaban
- Memberikan skor per soal (0–100)
- Menghasilkan file Excel berisi detail penilaian
- Menghasilkan file json untuk di gunakan di web
  
