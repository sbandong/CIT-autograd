# CIT-autograd

Install modul python yang diperlukan:
PyMuPDF
openai
pandas
openpyxl

Pada Command Prompt:

Jika run untuk pertama kali (Belum pernah ekstrak Kunci Jawaban):
python autograd.py --student_answer "Alamat file jawaban Siswa" --key_answer "Alamat file kunci jawaban"
Contoh:
python autograd.py --student_answer "student-answer\Jawaban_Mahasiswa_Sosial_Theory.pdf" --key_answer "key-answer\Kunci Jawaban Tugas Social Theory.pdf"

Jika sudah diekstrak kunci jawaban dan akan menilai jawaban lainnya:
python autograd.py --student_answer "Alamat file jawaban Siswa"
Contoh
python autograd.py --student_answer "student-answer\Jawaban_Mahasiswa_Sosial_Theory.pdf"

