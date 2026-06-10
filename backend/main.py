import re
from difflib import SequenceMatcher

try:
    # thefuzz dipakai untuk toleransi typo seperti: forbiden, databse, lemoot, conection
    from thefuzz import fuzz
    THEFUZZ_AVAILABLE = True
except ImportError:
    fuzz = None
    THEFUZZ_AVAILABLE = False

from flask import Flask, request, jsonify
from flask_cors import CORS
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

app = Flask(__name__)
CORS(app)

# Inisialisasi Sastrawi sekali saja agar tidak berat di setiap request
stemmer_factory = StemmerFactory()
stemmer = stemmer_factory.create_stemmer()

stopword_factory = StopWordRemoverFactory()
stopwords = set(stopword_factory.get_stop_words())

# ===============================
# KNOWLEDGE BASE: DAFTAR GEJALA
# ===============================
GEJALA = [
    {'id': 'G1', 'text': 'Tidak bisa di ping'},
    {'id': 'G2', 'text': 'Website blank'},
    {'id': 'G3', 'text': 'Internal Server Error'},
    {'id': 'G4', 'text': 'Service Unavailable'},
    {'id': 'G5', 'text': 'Connection Timeout'},
    {'id': 'G6', 'text': 'Server Not Found'},
    {'id': 'G7', 'text': 'Data tidak sempurna di load'},
    {'id': 'G8', 'text': 'Your clock is behind'},
    {'id': 'G9', 'text': 'Unable to connect'},
    {'id': 'G10', 'text': 'Phishing or Malicious Content Warnings'},
    {'id': 'G11', 'text': 'Your connection is not private'},
    {'id': 'G12', 'text': 'Network connection Refused'},
    {'id': 'G13', 'text': "The site can't be reached"},
    {'id': 'G14', 'text': 'Error establishing database connection'},
    {'id': 'G15', 'text': 'Server Forbidden'},
]

GEJALA_MAP = {g['id']: g['text'] for g in GEJALA}

# ===============================
# RULE BASE BERDASARKAN PAKAR
# ===============================
RULES = [
    {
        'kategori': 'Network',
        'gejala': ['G1', 'G5', 'G6', 'G9', 'G12', 'G13'],
        'solusi': 'Periksa koneksi internet dan konfigurasi jaringan. Cek DNS server, firewall, routing table, dan pastikan server dapat dijangkau. Lakukan traceroute untuk melacak titik putusnya koneksi. Hubungi ISP jika masalah pada jalur eksternal.',
    },
    {
        'kategori': 'Server',
        'gejala': ['G2', 'G3', 'G4', 'G5', 'G6', 'G11', 'G13', 'G14', 'G15'],
        'solusi': 'Periksa status layanan web server (Apache/Nginx). Cek log error server, restart service jika perlu. Pastikan konfigurasi virtual host benar, izin file/folder tepat, dan resource server (CPU/RAM) tidak penuh. Periksa SSL certificate jika ada.',
    },
    {
        'kategori': 'Database',
        'gejala': ['G7', 'G9', 'G14'],
        'solusi': 'Periksa status layanan database (MySQL/PostgreSQL). Cek kredensial koneksi di file konfigurasi, pastikan database aktif dan tidak penuh. Verifikasi nama host, port, user, dan password database. Lakukan repair pada tabel yang corrupt jika diperlukan.',
    },
    {
        'kategori': 'Komputer Pengguna',
        'gejala': ['G8', 'G10', 'G11'],
        'solusi': 'Sinkronkan waktu sistem komputer pengguna. Bersihkan cache dan cookies browser. Update browser ke versi terbaru. Cek apakah antivirus/ekstensi browser memblokir situs. Coba akses menggunakan browser atau perangkat lain untuk verifikasi.',
    },
    {
        'kategori': 'Scripting / Security',
        'gejala': ['G2', 'G3', 'G10', 'G15'],
        'solusi': 'Periksa kode skrip website dari error syntax maupun logic. Scan website dari malware/virus. Periksa izin file (chmod) agar tidak terlalu longgar. Pastikan konfigurasi .htaccess benar. Update CMS/plugin/framework ke versi terbaru dan ganti password admin.',
    },
    {
        'kategori': 'Frontend / Routing',
        'gejala': ['G2', 'G7', 'G13'],
        'solusi': 'Periksa konfigurasi routing pada framework (React Router, Vue Router, dll). Cek file .htaccess atau konfigurasi Nginx untuk URL rewriting. Pastikan aset frontend (JS/CSS) ter-load dengan benar. Periksa error console browser dan perbaiki broken link atau path yang salah.',
    },
]


# ===============================
# LABEL DAN PENJELASAN UNTUK USER UMUM
# ===============================
CATEGORY_INFO = {
    'Network': {
        'userTitle': 'Masalah Koneksi / Jaringan',
        'simpleExplanation': 'Website kemungkinan sulit dijangkau karena gangguan koneksi, DNS, firewall, atau jalur jaringan menuju server.',
        'solutionSteps': [
            'Coba akses website dari jaringan lain atau perangkat lain.',
            'Periksa koneksi internet dan DNS.',
            'Lakukan ping atau traceroute ke domain website.',
            'Periksa firewall atau aturan jaringan yang mungkin memblokir akses.'
        ]
    },
    'Server': {
        'userTitle': 'Masalah Server / Hosting',
        'simpleExplanation': 'Website kemungkinan bermasalah pada sisi server atau hosting, seperti service web mati, konfigurasi server salah, atau resource server penuh.',
        'solutionSteps': [
            'Periksa status web server seperti Apache atau Nginx.',
            'Cek log error server untuk melihat penyebab utama.',
            'Restart service server jika diperlukan.',
            'Periksa resource server seperti CPU, RAM, dan storage.'
        ]
    },
    'Database': {
        'userTitle': 'Masalah Database',
        'simpleExplanation': 'Website kemungkinan gagal mengambil atau menyimpan data karena koneksi database bermasalah.',
        'solutionSteps': [
            'Periksa apakah service database aktif.',
            'Cek host, port, username, password, dan nama database.',
            'Pastikan database tidak penuh atau corrupt.',
            'Periksa konfigurasi koneksi database pada aplikasi.'
        ]
    },
    'Komputer Pengguna': {
        'userTitle': 'Masalah Browser / Perangkat Pengguna',
        'simpleExplanation': 'Masalah kemungkinan berasal dari perangkat pengguna, browser, waktu sistem, cache, atau sertifikat yang terbaca tidak valid.',
        'solutionSteps': [
            'Pastikan tanggal dan jam perangkat sudah benar.',
            'Bersihkan cache dan cookies browser.',
            'Coba buka website memakai browser atau perangkat lain.',
            'Nonaktifkan sementara ekstensi browser yang mencurigakan.'
        ]
    },
    'Scripting / Security': {
        'userTitle': 'Masalah Script / Keamanan Website',
        'simpleExplanation': 'Website kemungkinan mengalami error pada kode program, konfigurasi keamanan, izin akses, atau terdeteksi konten berbahaya.',
        'solutionSteps': [
            'Periksa error pada kode aplikasi atau framework.',
            'Cek file permission dan konfigurasi .htaccess.',
            'Scan website dari malware atau file mencurigakan.',
            'Update CMS, plugin, framework, dan ganti password admin.'
        ]
    },
    'Frontend / Routing': {
        'userTitle': 'Masalah Tampilan / Routing Halaman',
        'simpleExplanation': 'Website kemungkinan bermasalah pada tampilan, file frontend, asset, atau pengaturan routing sehingga halaman tidak tampil normal.',
        'solutionSteps': [
            'Periksa console browser untuk melihat error JavaScript atau asset.',
            'Pastikan file CSS, JS, dan gambar berhasil dimuat.',
            'Cek konfigurasi routing pada framework frontend.',
            'Periksa rewrite rule pada .htaccess atau konfigurasi Nginx.'
        ]
    }
}

def certainty_label(pct: int) -> str:
    if pct >= 70:
        return 'Tinggi'
    if pct >= 40:
        return 'Sedang'
    return 'Rendah'

# =====================================================================
# KAMUS KNOWLEDGE ENGINEER + HYBRID LEXICON MATCHING
# ---------------------------------------------------------------------
# Struktur deteksi:
# 1. phrases  = frasa kuat/teknis/awam, bobot tinggi
# 2. groups   = kombinasi kata yang harus muncul bersama, bobot sedang
# 3. keywords = kata unik/kuat, bobot rendah-sedang
# 4. fuzzy    = toleransi typo memakai thefuzz sebagai fallback
#
# Catatan:
# - Jangan memakai kata umum seperti "server", "error", "website", "page",
#   "halaman", "masalah", atau "gagal" sebagai keyword tunggal.
# - Kata-kata umum boleh muncul di phrases/groups, tapi jangan berdiri sendiri.
# =====================================================================
SLANG_REPLACEMENTS = {
    # variasi tidak/bukan/bisa
    'gabisa': 'tidak bisa',
    'gbs': 'tidak bisa',
    'gk': 'tidak',
    'ga': 'tidak',
    'gak': 'tidak',
    'ngga': 'tidak',
    'nggak': 'tidak',
    'tdk': 'tidak',
    'tak': 'tidak',
    'bkn': 'bukan',

    # istilah web awam
    'web': 'website',
    'webnya': 'website',
    'situsnya': 'situs',
    'pagenya': 'halaman',
    'page': 'halaman',
    'laman': 'halaman',

    # istilah koneksi/akses
    'konek': 'connect',
    'koneksi': 'connect',
    'nyambung': 'terhubung',
    'tersambung': 'terhubung',
    'kebuka': 'buka',
    'dibuka': 'buka',
    'ngebuka': 'buka',
    'ngeload': 'loading',
    'muter': 'loading',
    'muter2': 'loading',
    'lemot': 'lambat',
    'lemoot': 'lambat',
    'lelet': 'lambat',
    'lola': 'lambat',

    # istilah database
    'db': 'database',
    'databse': 'database',
    'databasenya': 'database',
    'mysqlnya': 'mysql',

    # istilah security/certificate
    'sertif': 'sertifikat',
    'sertifkat': 'sertifikat',
    'cert': 'certificate',
    'forbiden': 'forbidden',
    'forbiddennya': 'forbidden',
}

NEGATION_CUES = {'bukan', 'tanpa'}
NEGATION_PHRASES = {
    'tidak muncul',
    'tidak ada',
    'bukan karena',
    'bukan error',
    'bukan masalah',
}

WEIGHTS = {
    'phrase': 1.00,
    'group': 0.75,
    'keyword': 0.50,
    'fuzzy_phrase': 0.65,
    'fuzzy_keyword': 0.30,
}

FUZZY_PHRASE_THRESHOLD = 88
FUZZY_KEYWORD_THRESHOLD = 92
MIN_SYMPTOM_SCORE = 0.45

SYMPTOM_PATTERNS = {
    'G1': {
        'phrases': [
            'tidak bisa di ping', 'tidak bisa ping', 'tidak dapat di ping',
            'ping gagal', 'gagal ping', 'ping tidak jalan', 'server tidak bisa diping',
            'server tidak merespon ping', 'request timed out saat ping',
            'ping request timeout', 'destination host unreachable', 'host unreachable',
            'rto saat ping', 'ping rto', 'ping putus', 'server tidak membalas ping'
        ],
        'groups': [['tidak', 'bisa', 'ping'], ['gagal', 'ping'], ['request', 'timed', 'out'], ['host', 'unreachable']],
        'keywords': ['ping', 'rto', 'unreachable']
    },
    'G2': {
        'phrases': [
            'website blank', 'halaman blank', 'halaman putih', 'layar putih',
            'cuma putih', 'hanya putih', 'tampil putih', 'blank putih',
            'website kosong', 'halaman kosong', 'layar kosong', 'tidak tampil apa apa',
            'tidak muncul apa apa', 'website tidak muncul', 'halaman tidak muncul',
            'isi website tidak muncul', 'konten tidak muncul', 'tampilan kosong',
            'website tidak ada isinya', 'halaman tidak keluar', 'ngebug putih'
        ],
        'groups': [['website', 'blank'], ['halaman', 'blank'], ['halaman', 'putih'], ['layar', 'putih'], ['konten', 'tidak', 'muncul']],
        'keywords': ['blank', 'putih', 'kosong']
    },
    'G3': {
        'phrases': [
            'internal server error', '500 internal server error', 'error 500',
            'http 500', 'server error 500', 'muncul error 500',
            'website error 500', 'halaman error 500', 'kesalahan internal server'
        ],
        'groups': [['internal', 'server', 'error'], ['error', '500'], ['http', '500']],
        'keywords': ['500']
    },
    'G4': {
        'phrases': [
            'service unavailable', '503 service unavailable', 'error 503', 'http 503',
            'layanan tidak tersedia', 'server tidak tersedia', 'website tidak tersedia',
            'service temporarily unavailable', 'temporarily unavailable',
            'server sedang tidak tersedia', 'website sedang tidak tersedia',
            'server sedang down', 'website sedang down'
        ],
        'groups': [['service', 'unavailable'], ['error', '503'], ['http', '503'], ['layanan', 'tidak', 'tersedia']],
        'keywords': ['503', 'unavailable']
    },
    'G5': {
        'phrases': [
            'connection timeout', 'request timeout', 'koneksi timeout',
            'waktu koneksi habis', 'koneksi habis waktu', 'website timeout',
            'loading lama', 'loading terus', 'loading tidak selesai',
            'website lambat', 'web lambat', 'website lemot', 'web lemot',
            'lama sekali dibuka', 'lama banget dibuka', 'susah loading',
            'halaman muter terus', 'browser loading terus', 'tidak selesai loading',
            'stuck loading', 'load lama banget', 'website berat dibuka',
            'respon website lama', 'aksesnya lambat', 'website lag', 'website ngelag', 'ngelag banget'
        ],
        'groups': [['connection', 'timeout'], ['request', 'timeout'], ['connect', 'timeout'], ['website', 'lambat'], ['loading', 'terus'], ['loading', 'lama'], ['website', 'lag']],
        'keywords': ['timeout', 'lambat', 'loading', 'stuck', 'lag']
    },
    'G6': {
        'phrases': [
            'server not found', 'server tidak ditemukan', 'website tidak ditemukan',
            'halaman tidak ditemukan', 'domain tidak ditemukan', '404 not found',
            'error 404', 'http 404', 'not found', 'alamat website tidak ditemukan',
            'situs tidak ditemukan', 'page not found', 'halaman 404',
            'muncul 404', 'website 404', 'dns not found', 'dns probe finished nxdomain',
            'dns_probe_finished_nxdomain', 'domain tidak ada', 'url tidak ditemukan'
        ],
        'groups': [['server', 'not', 'found'], ['not', 'found'], ['error', '404'], ['domain', 'tidak', 'ditemukan'], ['dns', 'nxdomain']],
        'keywords': ['404', 'nxdomain']
    },
    'G7': {
        'phrases': [
            'data tidak sempurna', 'data tidak tampil sempurna', 'data tidak lengkap',
            'data tidak muncul semua', 'data hanya muncul sebagian', 'konten tidak lengkap',
            'halaman tidak lengkap', 'halaman tidak termuat sempurna',
            'website tidak termuat sempurna', 'gambar tidak muncul', 'gambar tidak tampil',
            'css tidak load', 'css tidak terload', 'javascript tidak load',
            'javascript tidak jalan', 'js tidak jalan', 'tampilan berantakan',
            'layout berantakan', 'halaman rusak tampilannya', 'tabel tidak muncul',
            'menu tidak muncul', 'tombol tidak muncul', 'beberapa bagian website hilang',
            'asset tidak muncul', 'asset tidak load', 'style tidak muncul',
            'data kosong sebagian', 'isi website kepotong', 'halaman kepotong',
            'file css gagal dimuat', 'file js gagal dimuat', 'gambar broken'
        ],
        'groups': [['data', 'tidak', 'lengkap'], ['data', 'tidak', 'sempurna'], ['data', 'sebagian'], ['asset', 'tidak', 'load'], ['gambar', 'tidak', 'muncul'], ['tampilan', 'berantakan'], ['css', 'tidak', 'load'], ['javascript', 'tidak', 'jalan']],
        'keywords': ['sebagian', 'berantakan', 'kepotong', 'terpotong', 'asset', 'css', 'javascript', 'layout', 'broken']
    },
    'G8': {
        'phrases': [
            'your clock is behind', 'clock is behind', 'jam komputer salah',
            'jam laptop salah', 'tanggal komputer salah', 'tanggal laptop salah',
            'waktu perangkat salah', 'jam perangkat salah', 'waktu tidak sinkron',
            'tanggal tidak sesuai', 'masalah tanggal dan waktu',
            'browser bilang clock is behind', 'jam sistem salah', 'tanggal sistem salah',
            'waktu komputer tidak sesuai', 'jam tidak sesuai', 'tanggal tidak benar'
        ],
        'groups': [['clock', 'behind'], ['jam', 'salah'], ['tanggal', 'salah'], ['waktu', 'salah'], ['waktu', 'tidak', 'sinkron']],
        'keywords': ['clock']
    },
    'G9': {
        'phrases': [
            'unable to connect', 'tidak bisa connect', 'tidak bisa konek',
            'gagal connect', 'gagal konek', 'gagal terhubung',
            'tidak dapat terhubung', 'koneksi gagal', 'web tidak bisa tersambung',
            'website tidak bisa tersambung', 'website tidak bisa dihubungi',
            'gagal menghubungi server', 'tidak bisa menyambung ke website',
            'tidak tersambung ke server', 'koneksi ke website gagal',
            'koneksi ke server gagal', 'server tidak bisa dihubungi', 'gagal tersambung'
        ],
        'groups': [['unable', 'connect'], ['gagal', 'connect'], ['gagal', 'terhubung'], ['tidak', 'bisa', 'connect'], ['tidak', 'dapat', 'terhubung']],
        'keywords': ['connect', 'terhubung']
    },
    'G10': {
        'phrases': [
            'phishing warning', 'malicious content warning', 'situs berbahaya',
            'website berbahaya', 'terdeteksi phishing', 'terdeteksi malware',
            'terdeteksi virus', 'website kena malware', 'website kena virus',
            'browser memberi peringatan bahaya', 'website dianggap tidak aman',
            'situs mencurigakan', 'website mencurigakan', 'peringatan keamanan',
            'deceptive site ahead', 'harmful site', 'malware detected',
            'phishing detected', 'situs penipuan', 'website penipuan',
            'browser blokir website', 'google blokir website', 'peringatan situs berbahaya',
            'ada peringatan merah'
        ],
        'groups': [['peringatan', 'phishing'], ['peringatan', 'malware'], ['situs', 'berbahaya'], ['website', 'berbahaya'], ['malware', 'detected'], ['deceptive', 'site']],
        'keywords': ['phishing', 'malware', 'virus', 'malicious', 'berbahaya', 'mencurigakan', 'scam', 'penipuan']
    },
    'G11': {
        'phrases': [
            'your connection is not private', 'connection is not private',
            'koneksi tidak private', 'koneksi tidak pribadi', 'koneksi tidak aman',
            'ssl error', 'error ssl', 'certificate error', 'sertifikat error',
            'sertifikat tidak valid', 'sertifikat kadaluarsa', 'sertifikat expired',
            'masalah ssl', 'https error', 'privacy error', 'browser bilang tidak aman',
            'net err cert', 'net err cert authority invalid', 'net err cert date invalid',
            'koneksi bukan pribadi', 'sambungan tidak pribadi', 'ssl bermasalah',
            'sertifikat bermasalah', 'https bermasalah', 'certificate expired',
            'certificate invalid'
        ],
        'groups': [['connection', 'not', 'private'], ['koneksi', 'tidak', 'aman'], ['koneksi', 'tidak', 'pribadi'], ['ssl', 'error'], ['sertifikat', 'error'], ['certificate', 'error'], ['privacy', 'error']],
        'keywords': ['ssl', 'https', 'sertifikat', 'certificate', 'privacy']
    },
    'G12': {
        'phrases': [
            'connection refused', 'network connection refused', 'err connection refused',
            'err_connection_refused', 'koneksi ditolak', 'sambungan ditolak',
            'server menolak koneksi', 'website menolak koneksi', 'refused to connect',
            'localhost refused to connect', 'port ditolak', 'koneksi ke server ditolak',
            'server refused connection', 'website refused connection', 'firewall menolak koneksi',
            'port tidak menerima koneksi'
        ],
        'groups': [['connection', 'refused'], ['refused', 'connect'], ['connect', 'ditolak'], ['port', 'ditolak'], ['firewall', 'menolak']],
        'keywords': ['refused', 'ditolak']
    },
    'G13': {
        'phrases': [
            'the site cant be reached', 'the site cannot be reached',
            'this site cant be reached', 'this site cannot be reached',
            'situs tidak dapat dijangkau', 'website tidak bisa dijangkau',
            'website tidak dapat dijangkau', 'website tidak bisa dibuka',
            'tidak bisa buka website', 'gagal membuka website', 'susah masuk website',
            'susah masuk page', 'susah masuk halaman', 'halaman tidak bisa dibuka',
            'page tidak bisa dibuka', 'tidak bisa akses halaman', 'tidak bisa masuk halaman',
            'website tidak dapat diakses', 'web tidak dapat diakses',
            'halaman tidak kebuka', 'website tidak kebuka', 'gabisa akses web',
            'gabisa buka web', 'akses website gagal', 'link tidak bisa dibuka',
            'url tidak bisa dibuka', 'situs tidak terbuka', 'halaman gagal dibuka'
        ],
        'groups': [['site', 'cant', 'reached'], ['tidak', 'bisa', 'akses'], ['tidak', 'bisa', 'buka'], ['tidak', 'dapat', 'jangkau'], ['susah', 'masuk', 'halaman'], ['gagal', 'membuka', 'website']],
        'keywords': ['reached', 'jangkau']
    },
    'G14': {
        'phrases': [
            'error establishing database connection', 'establishing a database connection',
            'database connection error', 'error koneksi database', 'koneksi database gagal',
            'gagal konek database', 'tidak bisa konek database',
            'tidak bisa connect database', 'database tidak terhubung', 'database error',
            'db error', 'mysql error', 'sql error', 'koneksi mysql gagal',
            'gagal konek mysql', 'database down', 'website tidak bisa ambil data database',
            'gagal mengambil data dari database', 'tidak bisa mengambil data database',
            'koneksi db gagal', 'db tidak konek', 'database bermasalah',
            'mysql bermasalah', 'server database mati', 'database tidak jalan',
            'database tidak aktif', 'gagal terhubung ke database', 'koneksi sql bermasalah'
        ],
        'groups': [['database', 'connection'], ['connect', 'database'], ['koneksi', 'database'], ['mysql', 'error'], ['sql', 'error'], ['database', 'error'], ['database', 'bermasalah']],
        'keywords': ['database', 'mysql', 'sql']
    },
    'G15': {
        'phrases': [
            '403 forbidden', 'error 403', 'http 403', 'server forbidden',
            'access forbidden', 'akses dilarang', 'akses ditolak',
            'akses halaman ditolak', 'tidak punya izin akses',
            'tidak memiliki izin akses', 'permission denied',
            'dilarang mengakses halaman', 'halaman tidak diizinkan',
            'tidak bisa masuk karena forbidden', 'muncul forbidden',
            'website forbidden', 'page forbidden', 'forbidden access',
            'akses tidak diizinkan', 'hak akses ditolak',
            'tidak boleh mengakses halaman', 'server menolak akses',
            'halaman diblokir oleh permission', 'permission bermasalah'
        ],
        'groups': [['403', 'forbidden'], ['access', 'forbidden'], ['akses', 'ditolak'], ['akses', 'dilarang'], ['permission', 'denied'], ['izin', 'akses']],
        'keywords': ['403', 'forbidden', 'permission']
    }
}

# ===============================
# PREPROCESSING DAN DETEKSI GEJALA
# ===============================
def normalize_text(text: str) -> str:
    """Normalisasi teks user dan leksikon agar lebih mudah dicocokkan."""
    text = text.lower()
    text = text.replace("can't", "cant").replace("can’t", "cant")
    text = text.replace('cannot', 'cant')
    text = text.replace('_', ' ')

    # Bersihkan tanda baca awal agar replacement berbasis kata lebih aman.
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # Normalisasi slang/typo umum memakai word boundary agar tidak merusak kata lain.
    for wrong, correct in sorted(SLANG_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        text = re.sub(rf'\b{re.escape(wrong)}\b', correct, text)

    text = re.sub(r'\s+', ' ', text).strip()
    return text


def preprocess_text(user_text: str):
    text_clean = normalize_text(user_text)
    tokens = text_clean.split()
    tokens_no_stop = [word for word in tokens if word not in stopwords]
    tokens_stemmed = [stemmer.stem(word) for word in tokens_no_stop]
    tokens_stemmed_all = [stemmer.stem(word) for word in tokens]

    return {
        'original': user_text,
        'normalized': text_clean,
        'tokens': tokens,
        'tokens_no_stop': tokens_no_stop,
        'tokens_stemmed': tokens_stemmed,
        'tokens_stemmed_all': tokens_stemmed_all,
        'thefuzzAvailable': THEFUZZ_AVAILABLE,
    }


def similarity_ratio(a: str, b: str, mode: str = 'ratio') -> int:
    """Hitung kemiripan teks. Prioritas memakai thefuzz, fallback ke difflib."""
    if not a or not b:
        return 0

    if THEFUZZ_AVAILABLE:
        if mode == 'partial':
            return fuzz.partial_ratio(a, b)
        if mode == 'token_set':
            return fuzz.token_set_ratio(a, b)
        return fuzz.ratio(a, b)

    return int(SequenceMatcher(None, a, b).ratio() * 100)


def _contains_group(group, token_set, stem_set):
    for word in group:
        normalized_word = normalize_text(word)
        stemmed_word = stemmer.stem(normalized_word)
        if normalized_word not in token_set and stemmed_word not in stem_set:
            return False
    return True


def _is_negated(term: str, text_normalized: str) -> bool:
    """Cek apakah sebuah term dinegasikan, contoh: 'bukan error 500'.

    Catatan: frasa yang memang mengandung 'tidak', seperti 'tidak bisa buka website',
    tidak dianggap negasi karena 'tidak' adalah bagian dari gejala.
    """
    term_norm = normalize_text(term)
    if not term_norm or term_norm not in text_normalized:
        return False

    term_tokens = term_norm.split()
    if 'tidak' in term_tokens:
        return False

    tokens = text_normalized.split()
    n = len(term_tokens)

    for i in range(0, len(tokens) - n + 1):
        if tokens[i:i+n] == term_tokens:
            before = tokens[max(0, i-4):i]
            before_text = ' '.join(before)

            if any(cue in before for cue in NEGATION_CUES):
                return True
            if any(phrase in before_text for phrase in NEGATION_PHRASES):
                return True

    return False


def _append_evidence(evidence, method, candidate, normalized_candidate, weight, matched=True, fuzzy_score=None, threshold=None, status='accepted'):
    """Simpan bukti pencocokan agar proses deteksi bisa ditampilkan di frontend."""
    evidence.append({
        'method': method,
        'candidate': candidate,
        'normalizedCandidate': normalized_candidate,
        'matched': matched,
        'fuzzyScore': fuzzy_score,
        'threshold': threshold,
        'weight': weight,
        'status': status,
    })


def detect_symptoms(preprocess):
    text_normalized = preprocess['normalized']
    tokens = preprocess['tokens']
    token_set = set(tokens)
    stem_set = set(preprocess['tokens_stemmed_all'])

    detected = {}

    for symptom_id, pattern in SYMPTOM_PATTERNS.items():
        matched_by = []
        ignored_by_negation = []
        evidence = []
        top_fuzzy_phrases = []
        top_fuzzy_keywords = []
        score = 0.0

        # 1. Exact phrase matching, bukti paling kuat.
        for phrase in pattern.get('phrases', []):
            normalized_phrase = normalize_text(phrase)
            if normalized_phrase and normalized_phrase in text_normalized:
                if _is_negated(normalized_phrase, text_normalized):
                    ignored_by_negation.append(f"negasi frasa: {phrase}")
                    _append_evidence(
                        evidence,
                        method='Exact Phrase',
                        candidate=phrase,
                        normalized_candidate=normalized_phrase,
                        weight=0,
                        status='ignored_by_negation'
                    )
                    continue
                matched_by.append(f"frasa kuat: {phrase}")
                score += WEIGHTS['phrase']
                _append_evidence(
                    evidence,
                    method='Exact Phrase',
                    candidate=phrase,
                    normalized_candidate=normalized_phrase,
                    weight=WEIGHTS['phrase'],
                    status='accepted'
                )

        # 2. Group matching, beberapa kata harus muncul bersama.
        for group in pattern.get('groups', []):
            if _contains_group(group, token_set, stem_set):
                group_text = ' '.join(group)
                normalized_group = normalize_text(group_text)
                if _is_negated(group_text, text_normalized):
                    ignored_by_negation.append('negasi kombinasi kata: ' + ' + '.join(group))
                    _append_evidence(
                        evidence,
                        method='Group Words',
                        candidate=' + '.join(group),
                        normalized_candidate=normalized_group,
                        weight=0,
                        status='ignored_by_negation'
                    )
                    continue
                matched_by.append('kombinasi kata: ' + ' + '.join(group))
                score += WEIGHTS['group']
                _append_evidence(
                    evidence,
                    method='Group Words',
                    candidate=' + '.join(group),
                    normalized_candidate=normalized_group,
                    weight=WEIGHTS['group'],
                    status='accepted'
                )

        # 3. Keyword kuat/unik. Hindari keyword umum.
        for keyword in pattern.get('keywords', []):
            normalized_kw = normalize_text(keyword)
            stemmed_kw = stemmer.stem(normalized_kw)
            if normalized_kw in token_set or stemmed_kw in stem_set:
                if _is_negated(normalized_kw, text_normalized):
                    ignored_by_negation.append(f"negasi keyword: {keyword}")
                    _append_evidence(
                        evidence,
                        method='Strong Keyword',
                        candidate=keyword,
                        normalized_candidate=normalized_kw,
                        weight=0,
                        status='ignored_by_negation'
                    )
                    continue
                matched_by.append(f"keyword kuat: {keyword}")
                score += WEIGHTS['keyword']
                _append_evidence(
                    evidence,
                    method='Strong Keyword',
                    candidate=keyword,
                    normalized_candidate=normalized_kw,
                    weight=WEIGHTS['keyword'],
                    status='accepted'
                )

        # 4. Fuzzy phrase matching dengan thefuzz, fallback untuk typo.
        #    Selain accepted evidence, simpan top fuzzy candidates agar prosesnya terlihat.
        for phrase in pattern.get('phrases', []):
            normalized_phrase = normalize_text(phrase)
            if len(normalized_phrase) < 8 or normalized_phrase in text_normalized:
                continue
            fuzzy_score = similarity_ratio(normalized_phrase, text_normalized, mode='partial')
            if fuzzy_score >= 70:
                top_fuzzy_phrases.append({
                    'candidate': phrase,
                    'normalizedCandidate': normalized_phrase,
                    'fuzzyScore': fuzzy_score,
                    'threshold': FUZZY_PHRASE_THRESHOLD,
                    'accepted': fuzzy_score >= FUZZY_PHRASE_THRESHOLD,
                })

            if fuzzy_score >= FUZZY_PHRASE_THRESHOLD:
                if _is_negated(normalized_phrase, text_normalized):
                    ignored_by_negation.append(f"negasi fuzzy frasa: {phrase} ({fuzzy_score})")
                    _append_evidence(
                        evidence,
                        method='Fuzzy Phrase',
                        candidate=phrase,
                        normalized_candidate=normalized_phrase,
                        weight=0,
                        fuzzy_score=fuzzy_score,
                        threshold=FUZZY_PHRASE_THRESHOLD,
                        status='ignored_by_negation'
                    )
                    continue
                matched_by.append(f"fuzzy frasa: {phrase} ({fuzzy_score})")
                score += WEIGHTS['fuzzy_phrase']
                _append_evidence(
                    evidence,
                    method='Fuzzy Phrase',
                    candidate=phrase,
                    normalized_candidate=normalized_phrase,
                    weight=WEIGHTS['fuzzy_phrase'],
                    fuzzy_score=fuzzy_score,
                    threshold=FUZZY_PHRASE_THRESHOLD,
                    status='accepted'
                )

        # 5. Fuzzy keyword matching, hanya untuk kata cukup panjang dan bukan angka pendek.
        for keyword in pattern.get('keywords', []):
            normalized_kw = normalize_text(keyword)
            if len(normalized_kw) < 5 or normalized_kw.isdigit():
                continue
            best = 0
            best_token = None
            for token in tokens:
                if len(token) < 4:
                    continue
                ratio = similarity_ratio(normalized_kw, token, mode='ratio')
                if ratio > best:
                    best = ratio
                    best_token = token

            if best_token and best >= 70:
                top_fuzzy_keywords.append({
                    'candidate': keyword,
                    'matchedToken': best_token,
                    'fuzzyScore': best,
                    'threshold': FUZZY_KEYWORD_THRESHOLD,
                    'accepted': best >= FUZZY_KEYWORD_THRESHOLD,
                })

            if best >= FUZZY_KEYWORD_THRESHOLD:
                matched_by.append(f"fuzzy keyword: {keyword} ≈ {best_token} ({best})")
                score += WEIGHTS['fuzzy_keyword']
                _append_evidence(
                    evidence,
                    method='Fuzzy Keyword',
                    candidate=keyword,
                    normalized_candidate=normalized_kw,
                    weight=WEIGHTS['fuzzy_keyword'],
                    fuzzy_score=best,
                    threshold=FUZZY_KEYWORD_THRESHOLD,
                    status=f"accepted; matched token: {best_token}"
                )

        # Urutkan ringkasan fuzzy agar kandidat terbaik tampil dulu.
        top_fuzzy_phrases = sorted(top_fuzzy_phrases, key=lambda x: x['fuzzyScore'], reverse=True)[:5]
        top_fuzzy_keywords = sorted(top_fuzzy_keywords, key=lambda x: x['fuzzyScore'], reverse=True)[:5]

        if matched_by and score >= MIN_SYMPTOM_SCORE:
            confidence_percent = min(100, round(score * 45))
            if confidence_percent >= 75:
                confidence_label = 'Tinggi'
            elif confidence_percent >= 45:
                confidence_label = 'Sedang'
            else:
                confidence_label = 'Rendah'

            detected[symptom_id] = {
                'id': symptom_id,
                'text': GEJALA_MAP.get(symptom_id, symptom_id),
                'matchedBy': sorted(set(matched_by)),
                'ignoredByNegation': sorted(set(ignored_by_negation)),
                'confidenceScore': round(score, 2),
                'confidencePercent': confidence_percent,
                'confidenceLabel': confidence_label,
                'processDetail': {
                    'rawScoreBeforePercent': round(score, 2),
                    'minimumSymptomScore': MIN_SYMPTOM_SCORE,
                    'weights': WEIGHTS,
                    'thresholds': {
                        'fuzzyPhrase': FUZZY_PHRASE_THRESHOLD,
                        'fuzzyKeyword': FUZZY_KEYWORD_THRESHOLD,
                    },
                    'acceptedEvidence': evidence,
                    'topFuzzyPhraseCandidates': top_fuzzy_phrases,
                    'topFuzzyKeywordCandidates': top_fuzzy_keywords,
                }
            }
        elif evidence or ignored_by_negation or top_fuzzy_phrases or top_fuzzy_keywords:
            # Tidak masuk detected, tapi jejaknya tetap bisa dipakai jika suatu saat ingin debug semua gejala.
            # Saat ini tidak dikirim agar response tidak terlalu besar.
            pass

    return detected

# ===============================
# INFERENCE ENGINE BERBASIS RULE + TINGKAT KECOCOKAN
# ===============================
def diagnose_from_symptoms(selected_symptoms, detected_map=None):
    """Diagnosis berbasis rule + tingkat kecocokan gejala.

    Jika detected_map tersedia dari NLP, skor diagnosis ikut mempertimbangkan
    confidence tiap gejala. Untuk input manual, confidence dianggap 1.0.
    """
    selected_set = set(selected_symptoms)
    results = []

    for rule in RULES:
        matched = [g for g in rule['gejala'] if g in selected_set]
        if not matched:
            continue

        confidence_sum = 0.0
        for g in matched:
            if detected_map and g in detected_map:
                # confidenceScore bisa lebih dari 1 jika bukti banyak; dibatasi agar tidak terlalu dominan.
                confidence_sum += min(1.0, detected_map[g].get('confidenceScore', 1.0))
            else:
                confidence_sum += 1.0

        skor = confidence_sum / len(rule['gejala'])
        pct = round(skor * 100)

        info = CATEGORY_INFO.get(rule['kategori'], {})
        results.append({
            'kategori': rule['kategori'],
            'userTitle': info.get('userTitle', rule['kategori']),
            'simpleExplanation': info.get('simpleExplanation', ''),
            'solutionSteps': info.get('solutionSteps', []),
            'gejala': rule['gejala'],
            'solusi': rule['solusi'],
            'matched': matched,
            'matchedDetail': [
                {
                    'id': g,
                    'text': GEJALA_MAP.get(g, g),
                    'confidencePercent': detected_map.get(g, {}).get('confidencePercent') if detected_map else None,
                    'matchedBy': detected_map.get(g, {}).get('matchedBy', []) if detected_map else ['input manual']
                }
                for g in matched
            ],
            'skor': skor,
            'pct': pct,
            'certaintyLabel': certainty_label(pct),
            'reason': f"{len(matched)} dari {len(rule['gejala'])} gejala pada rule {rule['kategori']} terpenuhi."
        })

    # Urutan: jumlah gejala cocok lebih penting, lalu skor berbobot.
    results.sort(key=lambda x: (len(x['matched']), x['skor']), reverse=True)
    return results


def build_process_summary():
    return {
        'pipeline': [
            'Normalisasi slang dan tanda baca',
            'Tokenisasi dan stemming Sastrawi',
            'Exact phrase matching',
            'Group words matching',
            'Strong keyword matching',
            'Fuzzy matching dengan thefuzz sebagai fallback',
            'Negation handling',
            'Confidence scoring per gejala',
            'Rule-based diagnosis berdasarkan gejala terdeteksi'
        ],
        'weights': WEIGHTS,
        'thresholds': {
            'fuzzyPhrase': FUZZY_PHRASE_THRESHOLD,
            'fuzzyKeyword': FUZZY_KEYWORD_THRESHOLD,
            'minimumSymptomScore': MIN_SYMPTOM_SCORE,
        },
        'thefuzzAvailable': THEFUZZ_AVAILABLE,
        'note': 'Fuzzy dipakai sebagai fallback untuk typo. Exact phrase dan group words tetap menjadi bukti utama.'
    }

# ===============================
# ROUTES
# ===============================
@app.route('/api/gejala', methods=['GET'])
def get_gejala():
    return jsonify({'gejala': GEJALA})


@app.route('/api/diagnose', methods=['POST'])
def run_diagnose():
    data = request.get_json()
    if not data or 'selectedSymptoms' not in data:
        return jsonify({'error': 'Data tidak valid'}), 400

    selected = data['selectedSymptoms']
    if not selected:
        return jsonify({'error': 'Pilih minimal 1 gejala terlebih dahulu.'}), 400

    results = diagnose_from_symptoms(selected)
    if not results:
        return jsonify({'showWarning': True, 'results': None})

    return jsonify({
        'showWarning': False,
        'detectedSymptoms': [{'id': g, 'text': GEJALA_MAP.get(g, g), 'matchedBy': ['input manual']} for g in selected],
        'results': results,
        'mainResult': results[0],
        'alternativeResults': results[1:],
        'processSummary': build_process_summary()
    })


@app.route('/api/nlp-diagnose', methods=['POST'])
def run_nlp_diagnose():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': "Data tidak valid. Kirim JSON dengan key 'text'."}), 400

    user_text = data['text']
    if not user_text.strip():
        return jsonify({'error': 'Pesan tidak boleh kosong.'}), 400

    preprocess = preprocess_text(user_text)
    detected_map = detect_symptoms(preprocess)
    detected_symptoms = sorted(detected_map.keys(), key=lambda x: int(x[1:]))

    print('Original:', user_text)
    print('Normalized:', preprocess['normalized'])
    print('Tokens:', preprocess['tokens'])
    print('Tokens Stemmed:', preprocess['tokens_stemmed'])
    print('Detected Symptoms:', detected_symptoms)

    if not detected_symptoms:
        return jsonify({
            'showWarning': True,
            'results': None,
            'preprocessing': preprocess,
            'detectedSymptoms': [],
            'processSummary': build_process_summary()
        })

    results = diagnose_from_symptoms(detected_symptoms, detected_map)
    if not results:
        return jsonify({
            'showWarning': True,
            'results': None,
            'preprocessing': preprocess,
            'detectedSymptoms': list(detected_map.values()),
            'processSummary': build_process_summary()
        })

    return jsonify({
        'showWarning': False,
        'preprocessing': preprocess,
        'detectedSymptoms': [detected_map[g] for g in detected_symptoms],
        'results': results,
        'mainResult': results[0],
        'alternativeResults': results[1:],
        'processSummary': build_process_summary()
    })


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
