# Sistem Pakar Diagnosa Kerusakan Website

Aplikasi ini merupakan sistem pakar untuk membantu mendiagnosa kerusakan pada website berdasarkan keluhan pengguna. Sistem menggunakan pendekatan **rule-based expert system**, **NLP sederhana**, dan **forward chaining berbasis tingkat kecocokan gejala**.

Pengguna dapat mengetik keluhan dengan bahasa bebas, misalnya:

> "Website saya blank putih dan loading terus"

Kemudian sistem akan memproses teks tersebut, mendeteksi gejala, menentukan kemungkinan kerusakan, dan memberikan solusi perbaikan.

---

## Fitur Utama

* Input keluhan menggunakan bahasa natural
* Preprocessing teks:

  * Case folding
  * Cleaning
  * Tokenization
  * Stopword removal
  * Stemming
* Deteksi gejala berdasarkan leksikon teknis dan bahasa awam
* Diagnosis kerusakan website berdasarkan rule pakar
* Menampilkan diagnosis utama dan kemungkinan alternatif
* Menampilkan solusi perbaikan
* Tampilan chat sederhana dan mudah dipahami
* Mendukung dark mode

---

## Teknologi yang Digunakan

### Frontend

* React
* TypeScript
* Tailwind CSS
* Lucide React

### Backend

* Python
* Flask
* Flask-CORS
* Sastrawi

---

## Kategori Kerusakan

Sistem dapat mendeteksi 6 kategori kerusakan website:

1. Network / Jaringan
2. Server / Hosting
3. Database
4. Komputer Pengguna
5. Scripting / Security
6. Frontend / Routing

---

## Daftar Gejala

| Kode | Gejala                                 |
| ---- | -------------------------------------- |
| G1   | Tidak bisa di ping                     |
| G2   | Website blank                          |
| G3   | Internal Server Error                  |
| G4   | Service Unavailable                    |
| G5   | Connection Timeout                     |
| G6   | Server Not Found                       |
| G7   | Data tidak sempurna di load            |
| G8   | Your clock is behind                   |
| G9   | Unable to connect                      |
| G10  | Phishing or Malicious Content Warnings |
| G11  | Your connection is not private         |
| G12  | Network connection Refused             |
| G13  | The site can't be reached              |
| G14  | Error establishing database connection |
| G15  | Server Forbidden                       |

---

## Rule Pakar

Rule berikut digunakan sebagai basis pengetahuan sistem:

| Kategori             | Gejala                                 |
| -------------------- | -------------------------------------- |
| Network              | G1, G5, G6, G9, G12, G13               |
| Server               | G2, G3, G4, G5, G6, G11, G13, G14, G15 |
| Database             | G7, G9, G14                            |
| Komputer Pengguna    | G8, G10, G11                           |
| Scripting / Security | G2, G3, G10, G15                       |
| Frontend / Routing   | G2, G7, G13                            |

---

## Alur Sistem

```text
Input Keluhan User
        ↓
Preprocessing NLP
        ↓
Deteksi Kata Kunci / Frasa
        ↓
Konversi ke Gejala G1-G15
        ↓
Pencocokan Rule Pakar
        ↓
Diagnosis Kerusakan Website
        ↓
Solusi Perbaikan
```

---

## Cara Kerja Singkat

1. User mengetik keluhan website.
2. Sistem melakukan preprocessing teks.
3. Sistem mencocokkan teks dengan leksikon gejala.
4. Gejala yang terdeteksi dicocokkan dengan rule pakar.
5. Sistem menghitung tingkat kecocokan gejala.
6. Sistem menampilkan diagnosis utama, diagnosis alternatif, dan solusi.

---

## Contoh Input dan Output

### Contoh 1

Input:

```text
Website saya blank putih dan tidak muncul apa-apa.
```

Gejala terdeteksi:

```text
G2 - Website blank
```

Kemungkinan diagnosis:

```text
Frontend / Routing
Server
Scripting / Security
```

---

### Contoh 2

Input:

```text
Website muncul error establishing database connection.
```

Gejala terdeteksi:

```text
G14 - Error establishing database connection
```

Kemungkinan diagnosis:

```text
Database
Server
```

---

### Contoh 3

Input:

```text
Website saya lemot, loading terus, dan connection timeout.
```

Gejala terdeteksi:

```text
G5 - Connection Timeout
```

Kemungkinan diagnosis:

```text
Network
Server
```

---

## Instalasi Backend

Masuk ke folder backend:

```bash
cd backend
```

Buat virtual environment:

```bash
python -m venv venv
```

Aktifkan virtual environment:

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

Install dependency:

```bash
pip install flask flask-cors sastrawi
```

Jalankan backend:

```bash
python main.py
```

Backend berjalan pada:

```text
http://127.0.0.1:8000
```

---

## Instalasi Frontend

Masuk ke folder frontend:

```bash
cd frontend
```

Install dependency:

```bash
npm install
```

Jalankan frontend:

```bash
npm run dev
```

Frontend berjalan pada:

```text
http://localhost:5173
```

---

## Endpoint API

### 1. Get Daftar Gejala

```http
GET /api/gejala
```

Response:

```json
{
  "gejala": [
    {
      "id": "G1",
      "text": "Tidak bisa di ping"
    }
  ]
}
```

---

### 2. Diagnosis Manual

```http
POST /api/diagnose
```

Body:

```json
{
  "selectedSymptoms": ["G2", "G7"]
}
```

---

### 3. Diagnosis dari Teks NLP

```http
POST /api/nlp-diagnose
```

Body:

```json
{
  "text": "Website saya blank putih dan loading terus"
}
```

---

## Contoh Kasus Uji

| No | Input User                                             | Gejala Harapan | Diagnosis Harapan             |
| -- | ------------------------------------------------------ | -------------- | ----------------------------- |
| 1  | Website saya tidak bisa di ping dan connection timeout | G1, G5         | Network                       |
| 2  | Website muncul internal server error 500               | G3             | Server / Scripting            |
| 3  | Website service unavailable 503                        | G4             | Server                        |
| 4  | Website error establishing database connection         | G14            | Database / Server             |
| 5  | Data website hanya tampil sebagian                     | G7             | Database / Frontend           |
| 6  | Jam laptop salah, muncul your clock is behind          | G8             | Komputer Pengguna             |
| 7  | Your connection is not private                         | G11            | Komputer Pengguna / Server    |
| 8  | Website terdeteksi phishing                            | G10            | Scripting / Security          |
| 9  | Website muncul 403 forbidden                           | G15            | Server / Scripting            |
| 10 | Website blank putih kosong                             | G2             | Frontend / Server / Scripting |

---

## Catatan Metode

Sistem ini tidak menggunakan forward chaining murni yang terlalu kaku. Hal tersebut dilakukan karena input pengguna berbentuk teks bebas, sehingga gejala yang terdeteksi dapat bervariasi.

Oleh karena itu, sistem menggunakan pendekatan:

```text
Rule-Based Expert System + NLP + Tingkat Kecocokan Gejala
```

Pendekatan ini membuat sistem tetap berbasis pengetahuan pakar, tetapi lebih fleksibel dalam menerima bahasa awam dari pengguna.

---

## Struktur Project

```text
project/
│
├── backend/
│   └── main.py
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── styles/
│   │       └── index.css
│   │
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

---

## Pengembangan Selanjutnya

Beberapa fitur yang dapat dikembangkan:

* Menambahkan data uji lebih banyak
* Menambahkan bobot keyakinan pada setiap gejala
* Menambahkan fitur export hasil diagnosis
* Menambahkan dashboard admin untuk mengelola rule
* Menambahkan database untuk menyimpan riwayat diagnosis
* Menambahkan validasi hasil oleh pakar

---

## Kesimpulan

Aplikasi ini dapat membantu pengguna umum dalam melakukan diagnosis awal terhadap kerusakan website. Dengan kombinasi sistem pakar, rule pakar, dan NLP sederhana, sistem mampu memahami keluhan pengguna, mendeteksi gejala, dan memberikan solusi perbaikan yang mudah dipahami.
