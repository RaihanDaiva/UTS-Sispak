import re
from difflib import SequenceMatcher
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
# KAMUS KNOWLEDGE ENGINEER - VERSI DIPERLUAS
# Tujuan:
# 1) Menangkap bahasa teknis error website.
# 2) Menangkap bahasa awam seperti "web lemot", "halaman putih", "susah masuk page".
# 3) Menangkap slang ringan seperti "gak bisa", "ga bisa", "gabisa", "kebuka", "konek".
#
# phrases  = frasa kuat, dicek langsung dari kalimat normalisasi.
# groups   = kombinasi kata yang harus muncul bersama.
# keywords = kata unik/kuat. Hindari kata terlalu umum seperti "server", "error",
#            "website", "web", "page", "halaman", "gagal", dan "masalah" sendirian.
# =====================================================================

# Normalisasi tambahan agar variasi bahasa awam lebih mudah terbaca.
# Contoh: "gabisa buka web" -> "tidak bisa buka web"
SLANG_REPLACEMENTS = {
    "nggak": "tidak",
    "gak": "tidak",
    "ga": "tidak",
    "gk": "tidak",
    "gx": "tidak",
    "tdk": "tidak",
    "tak": "tidak",
    "gabisa": "tidak bisa",
    "gbs": "tidak bisa",
    "ngga": "tidak",
    "nggk": "tidak",
    "engga": "tidak",
    "enggak": "tidak",
    "kagak": "tidak",
    "konek": "connect",
    "koneksi": "connection",
    "nyambung": "terhubung",
    "tersambung": "terhubung",
    "kebuka": "buka",
    "ngebuka": "buka",
    "dibuka": "buka",
    "ngeload": "loading",
    "ngeloding": "loading",
    "muter": "loading",
    "muter2": "loading",
    "lemot": "lambat",
    "lelet": "lambat",
    "lola": "lambat",
    "down": "tidak tersedia",
    "db": "database",
    "dB": "database",
    "mysql": "mysql",
    "sql": "sql"
}

SYMPTOM_PATTERNS = {
    'G1': {
        'label_awam': 'Website atau server tidak merespons ping',
        'phrases': [
            'tidak bisa di ping', 'tidak dapat di ping', 'tidak bisa ping', 'tidak dapat ping',
            'gagal ping', 'ping gagal', 'ping tidak jalan', 'ping tidak berhasil',
            'server tidak bisa diping', 'server tidak bisa di ping', 'server tidak merespon ping',
            'server tidak membalas ping', 'tidak ada balasan ping', 'ping ke server gagal',
            'request timed out', 'request timeout saat ping', 'ping request timeout',
            'destination host unreachable', 'host unreachable', 'network unreachable',
            'rto saat ping', 'ping rto', 'rto ping', 'ping timeout', 'ping putus',
            'icmp timeout', 'icmp tidak respon'
        ],
        'groups': [
            ['tidak', 'bisa', 'ping'], ['tidak', 'dapat', 'ping'], ['gagal', 'ping'],
            ['ping', 'timeout'], ['ping', 'rto'], ['server', 'ping', 'gagal'],
            ['host', 'unreachable'], ['destination', 'host', 'unreachable']
        ],
        'keywords': ['rto', 'icmp']
    },

    'G2': {
        'label_awam': 'Website kosong atau hanya tampil putih',
        'phrases': [
            'website blank', 'web blank', 'halaman blank', 'page blank', 'blank page',
            'website putih', 'web putih', 'halaman putih', 'page putih', 'layar putih',
            'cuma putih', 'hanya putih', 'tampil putih', 'blank putih',
            'web kosong', 'website kosong', 'halaman kosong', 'page kosong', 'layar kosong',
            'tidak tampil apa apa', 'tidak muncul apa apa', 'tidak ada apa apa',
            'website tidak muncul', 'web tidak muncul', 'halaman tidak muncul',
            'isi website tidak muncul', 'isi web tidak muncul', 'konten tidak muncul',
            'website tidak ada isinya', 'web tidak ada isinya', 'halaman tidak ada isinya',
            'cuma layar kosong', 'tampilan kosong', 'web tidak menampilkan konten',
            'halaman tidak keluar', 'konten tidak keluar', 'web hanya blank',
            'website hanya blank', 'ngebug putih', 'white screen', 'white screen of death',
            'layar website putih', 'halaman website putih'
        ],
        'groups': [
            ['website', 'blank'], ['web', 'blank'], ['halaman', 'blank'], ['page', 'blank'],
            ['halaman', 'putih'], ['layar', 'putih'], ['website', 'kosong'],
            ['halaman', 'kosong'], ['konten', 'tidak', 'muncul'],
            ['tidak', 'muncul', 'apa'], ['tidak', 'tampil', 'apa']
        ],
        'keywords': ['blank']
    },

    'G3': {
        'label_awam': 'Muncul error 500 atau internal server error',
        'phrases': [
            'internal server error', '500 internal server error', 'internal error 500',
            'error 500', 'http 500', 'status 500', 'kode 500', 'server error 500',
            'muncul error 500', 'website error 500', 'web error 500', 'page error 500',
            'halaman error 500', 'kesalahan internal server', 'server mengalami internal error',
            'ada tulisan internal server error', 'muncul pesan internal server error',
            'pesan internal server error', '500 server error', 'server internal error',
            'http status 500', 'response 500', '500 error'
        ],
        'groups': [
            ['internal', 'server', 'error'], ['server', 'error', '500'],
            ['http', '500'], ['status', '500'], ['kode', '500']
        ],
        'keywords': ['500']
    },

    'G4': {
        'label_awam': 'Layanan website sedang tidak tersedia',
        'phrases': [
            'service unavailable', '503 service unavailable', 'service temporarily unavailable',
            'temporarily unavailable', 'error 503', 'http 503', 'status 503', 'kode 503',
            'layanan tidak tersedia', 'server tidak tersedia', 'website tidak tersedia',
            'web tidak tersedia', 'server sedang tidak tersedia', 'website sedang tidak tersedia',
            'web sedang tidak tersedia', 'layanan sedang gangguan', 'server sedang gangguan',
            'server sedang penuh', 'server sedang overload', 'server overload',
            'server sedang down', 'website sedang down', 'web sedang down',
            'server tidak bisa melayani request', 'layanan sementara tidak tersedia',
            'website sementara tidak tersedia', '503 error'
        ],
        'groups': [
            ['service', 'unavailable'], ['503', 'service'], ['layanan', 'tidak', 'tersedia'],
            ['server', 'tidak', 'tersedia'], ['website', 'tidak', 'tersedia'],
            ['server', 'overload'], ['server', 'down']
        ],
        'keywords': ['503', 'unavailable', 'overload']
    },

    'G5': {
        'label_awam': 'Website lambat atau loading terlalu lama',
        'phrases': [
            'connection timeout', 'request timeout', 'koneksi timeout', 'connection timed out',
            'website timeout', 'web timeout', 'page timeout', 'halaman timeout',
            'waktu koneksi habis', 'koneksi habis waktu', 'batas waktu koneksi habis',
            'loading lama', 'loading lama sekali', 'loading lama banget', 'loading terus',
            'loading tidak selesai', 'tidak selesai loading', 'stuck loading',
            'website lemot', 'web lemot', 'website lambat', 'web lambat', 'page lambat',
            'halaman lambat', 'akses website lambat', 'akses web lambat',
            'lama sekali dibuka', 'lama banget dibuka', 'lama dibuka', 'susah loading',
            'halaman muter terus', 'browser loading terus', 'loading muter terus',
            'membuka website lama', 'membuka web lama', 'website berat dibuka',
            'web berat dibuka', 'respon website lama', 'respon web lama',
            'page lama terbuka', 'halaman lama terbuka', 'web lelet', 'website lelet',
            'web lola', 'website lola', 'proses buka web lama', 'website tidak kunjung terbuka',
            'web tidak kunjung terbuka', 'menunggu respon terlalu lama', 'taking too long to respond',
            'took too long to respond', 'site took too long to respond'
        ],
        'groups': [
            ['connection', 'timeout'], ['request', 'timeout'], ['website', 'lambat'],
            ['web', 'lambat'], ['loading', 'lama'], ['loading', 'terus'],
            ['halaman', 'loading', 'terus'], ['browser', 'loading', 'terus'],
            ['respon', 'lama'], ['terlalu', 'lama'], ['time', 'out']
        ],
        'keywords': ['timeout', 'lambat', 'loading']
    },

    'G6': {
        'label_awam': 'Server, domain, atau halaman tidak ditemukan',
        'phrases': [
            'server not found', 'server tidak ditemukan', 'website tidak ditemukan',
            'web tidak ditemukan', 'halaman tidak ditemukan', 'page tidak ditemukan',
            'domain tidak ditemukan', 'situs tidak ditemukan', 'alamat web tidak ditemukan',
            'alamat website tidak ditemukan', 'url tidak ditemukan', 'link tidak ditemukan',
            '404 not found', 'not found 404', 'error 404', 'http 404', 'status 404',
            'kode 404', 'page not found', 'halaman 404', 'muncul 404', 'website 404',
            'web 404', '404 error', 'dns not found', 'domain not found',
            'dns_probe_finished_nxdomain', 'nxdomain', 'nama domain tidak ditemukan',
            'domain tidak ada', 'halaman tidak ada', 'page tidak ada'
        ],
        'groups': [
            ['server', 'not', 'found'], ['not', 'found', '404'], ['404', 'not', 'found'],
            ['domain', 'tidak', 'ditemukan'], ['halaman', 'tidak', 'ditemukan'],
            ['page', 'tidak', 'ditemukan'], ['dns', 'not', 'found']
        ],
        'keywords': ['404', 'nxdomain']
    },

    'G7': {
        'label_awam': 'Data, gambar, atau tampilan website tidak lengkap',
        'phrases': [
            'data tidak sempurna', 'data tidak tampil sempurna', 'data tidak lengkap',
            'data tidak muncul semua', 'data hanya muncul sebagian', 'data kosong sebagian',
            'konten tidak lengkap', 'konten tampil sebagian', 'konten terpotong',
            'halaman tidak lengkap', 'halaman tidak termuat sempurna',
            'website tidak termuat sempurna', 'web tidak termuat sempurna',
            'website tampil sebagian', 'web tampil sebagian', 'isi web kepotong',
            'halaman kepotong', 'tampilan kepotong', 'gambar tidak muncul',
            'gambar tidak tampil', 'gambar broken', 'broken image', 'ikon tidak muncul',
            'icon tidak muncul', 'css tidak load', 'css tidak terload', 'css gagal dimuat',
            'file css gagal dimuat', 'javascript tidak load', 'javascript tidak jalan',
            'js tidak load', 'js tidak jalan', 'file js gagal dimuat',
            'tampilan berantakan', 'layout berantakan', 'tampilan tidak rapi',
            'halaman rusak tampilannya', 'website rusak tampilannya', 'tabel tidak muncul',
            'menu tidak muncul', 'tombol tidak muncul', 'beberapa bagian website hilang',
            'beberapa bagian web hilang', 'asset tidak muncul', 'asset tidak load',
            'asset tidak termuat', 'style tidak muncul', 'style tidak jalan',
            'halaman tidak ter-render sempurna', 'render tidak sempurna'
        ],
        'groups': [
            ['data', 'tidak', 'lengkap'], ['data', 'tidak', 'sempurna'],
            ['data', 'muncul', 'sebagian'], ['gambar', 'tidak', 'muncul'],
            ['css', 'tidak', 'load'], ['javascript', 'tidak', 'jalan'],
            ['js', 'tidak', 'jalan'], ['tampilan', 'berantakan'],
            ['layout', 'berantakan'], ['asset', 'tidak', 'load'],
            ['konten', 'tidak', 'lengkap'], ['menu', 'tidak', 'muncul']
        ],
        'keywords': ['sebagian', 'berantakan', 'kepotong', 'terpotong', 'asset', 'css', 'javascript', 'layout']
    },

    'G8': {
        'label_awam': 'Jam, tanggal, atau waktu perangkat salah',
        'phrases': [
            'your clock is behind', 'clock is behind', 'jam komputer salah',
            'jam laptop salah', 'jam perangkat salah', 'jam sistem salah',
            'tanggal komputer salah', 'tanggal laptop salah', 'tanggal perangkat salah',
            'tanggal sistem salah', 'waktu komputer salah', 'waktu laptop salah',
            'waktu perangkat salah', 'waktu tidak sinkron', 'jam tidak sinkron',
            'tanggal tidak sesuai', 'jam tidak sesuai', 'waktu tidak sesuai',
            'tanggal tidak benar', 'jam tidak benar', 'masalah tanggal dan waktu',
            'browser bilang clock is behind', 'perangkat tidak sinkron waktu',
            'setelan waktu salah', 'setting waktu salah', 'waktu sistem tidak sesuai'
        ],
        'groups': [
            ['clock', 'behind'], ['jam', 'salah'], ['tanggal', 'salah'],
            ['waktu', 'salah'], ['jam', 'tidak', 'sesuai'],
            ['tanggal', 'tidak', 'sesuai'], ['waktu', 'tidak', 'sinkron']
        ],
        'keywords': ['clock']
    },

    'G9': {
        'label_awam': 'Website gagal terhubung ke server',
        'phrases': [
            'unable to connect', 'tidak bisa connect', 'tidak bisa konek',
            'tidak dapat connect', 'tidak dapat konek', 'gagal connect',
            'gagal konek', 'gagal koneksi', 'koneksi gagal', 'gagal terhubung',
            'tidak dapat terhubung', 'tidak bisa terhubung', 'gagal tersambung',
            'tidak tersambung ke server', 'web tidak bisa tersambung',
            'website tidak bisa tersambung', 'website tidak bisa dihubungi',
            'web tidak bisa dihubungi', 'server tidak bisa dihubungi',
            'gagal menghubungi server', 'tidak bisa menyambung ke website',
            'koneksi ke website gagal', 'koneksi ke web gagal', 'koneksi ke server gagal',
            'website tidak merespon koneksi', 'web tidak merespon koneksi',
            'cannot connect to server', 'cant connect to server', 'could not connect',
            'failed to connect', 'failed to connect to server'
        ],
        'groups': [
            ['unable', 'connect'], ['gagal', 'connection'], ['gagal', 'terhubung'],
            ['tidak', 'bisa', 'connect'], ['tidak', 'dapat', 'connect'],
            ['server', 'tidak', 'bisa', 'dihubungi'],
            ['failed', 'connect'], ['could', 'not', 'connect']
        ],
        'keywords': []
    },

    'G10': {
        'label_awam': 'Website terdeteksi berbahaya, malware, atau phishing',
        'phrases': [
            'phishing warning', 'malicious content warning', 'peringatan phishing',
            'peringatan malware', 'peringatan virus', 'peringatan keamanan',
            'konten berbahaya', 'situs berbahaya', 'website berbahaya',
            'web berbahaya', 'situs mencurigakan', 'website mencurigakan',
            'web mencurigakan', 'website dianggap tidak aman', 'situs dianggap tidak aman',
            'terdeteksi phishing', 'terdeteksi malware', 'terdeteksi virus',
            'malware detected', 'phishing detected', 'harmful site', 'deceptive site ahead',
            'situs penipuan', 'website penipuan', 'web penipuan',
            'website kena malware', 'web kena malware', 'website kena virus',
            'web kena virus', 'browser memberi peringatan bahaya',
            'browser blokir website', 'browser memblokir website',
            'google blokir website', 'google memblokir website',
            'website diblokir karena malware', 'ada peringatan merah',
            'peringatan situs berbahaya', 'situs tidak aman karena malware',
            'unsafe site', 'dangerous site'
        ],
        'groups': [
            ['peringatan', 'phishing'], ['peringatan', 'malware'],
            ['situs', 'bahaya'], ['website', 'bahaya'], ['web', 'bahaya'],
            ['terdeteksi', 'malware'], ['terdeteksi', 'phishing'],
            ['website', 'kena', 'virus'], ['website', 'kena', 'malware'],
            ['browser', 'blokir', 'website']
        ],
        'keywords': ['phishing', 'malware', 'malicious', 'scam']
    },

    'G11': {
        'label_awam': 'Koneksi tidak aman atau sertifikat SSL bermasalah',
        'phrases': [
            'your connection is not private', 'connection is not private',
            'koneksi tidak private', 'koneksi tidak pribadi', 'koneksi bukan pribadi',
            'sambungan tidak pribadi', 'koneksi tidak aman', 'sambungan tidak aman',
            'ssl error', 'error ssl', 'ssl bermasalah', 'masalah ssl',
            'https error', 'https bermasalah', 'certificate error',
            'certificate invalid', 'certificate expired', 'sertifikat error',
            'sertifikat bermasalah', 'sertifikat tidak valid', 'sertifikat kadaluarsa',
            'sertifikat expired', 'browser menolak sertifikat',
            'website tidak aman karena sertifikat', 'privacy error',
            'net err cert', 'net err cert authority invalid', 'net err cert date invalid',
            'err cert authority invalid', 'err cert date invalid',
            'browser bilang tidak aman', 'situs tidak aman karena ssl',
            'ssl certificate problem', 'invalid certificate', 'expired certificate'
        ],
        'groups': [
            ['connection', 'not', 'private'], ['koneksi', 'tidak', 'aman'],
            ['koneksi', 'tidak', 'pribadi'], ['ssl', 'error'],
            ['ssl', 'bermasalah'], ['sertifikat', 'tidak', 'valid'],
            ['sertifikat', 'kadaluarsa'], ['certificate', 'expired'],
            ['certificate', 'invalid'], ['privacy', 'error']
        ],
        'keywords': ['ssl', 'certificate', 'sertifikat']
    },

    'G12': {
        'label_awam': 'Koneksi ditolak oleh server, port, atau firewall',
        'phrases': [
            'network connection refused', 'connection refused', 'err_connection_refused',
            'refused to connect', 'server refused connection', 'website refused connection',
            'localhost refused to connect', 'koneksi ditolak', 'sambungan ditolak',
            'server menolak koneksi', 'website menolak koneksi', 'web menolak koneksi',
            'koneksi ke server ditolak', 'akses koneksi ditolak',
            'permintaan koneksi ditolak', 'server menolak request',
            'port ditolak', 'port tidak menerima koneksi',
            'firewall menolak koneksi', 'firewall menolak akses',
            'akses ditolak jaringan', 'koneksi ditolak firewall'
        ],
        'groups': [
            ['connection', 'refused'], ['refused', 'connect'],
            ['koneksi', 'ditolak'], ['sambungan', 'ditolak'],
            ['server', 'menolak', 'koneksi'], ['port', 'ditolak'],
            ['firewall', 'menolak', 'koneksi']
        ],
        'keywords': ['refused']
    },

    'G13': {
        'label_awam': 'Website atau halaman tidak bisa dibuka',
        'phrases': [
            'the site cant be reached', 'the site cannot be reached',
            'this site cant be reached', 'this site cannot be reached',
            'site cant be reached', 'situs tidak dapat dijangkau',
            'website tidak bisa dijangkau', 'web tidak bisa dijangkau',
            'website tidak dapat dijangkau', 'web tidak dapat dijangkau',
            'website tidak bisa dibuka', 'web tidak bisa dibuka',
            'website tidak dapat dibuka', 'web tidak dapat dibuka',
            'tidak bisa buka website', 'tidak bisa buka web',
            'tidak dapat buka website', 'tidak dapat buka web',
            'gagal membuka website', 'gagal membuka web',
            'susah masuk website', 'susah masuk web', 'susah masuk page',
            'susah masuk halaman', 'halaman tidak bisa dibuka',
            'page tidak bisa dibuka', 'halaman tidak dapat dibuka',
            'page tidak dapat dibuka', 'tidak bisa akses halaman',
            'tidak bisa akses website', 'tidak bisa akses web',
            'tidak bisa masuk halaman', 'tidak bisa masuk page',
            'website tidak dapat diakses', 'web tidak dapat diakses',
            'website tidak bisa diakses', 'web tidak bisa diakses',
            'page tidak kebuka', 'halaman tidak kebuka',
            'website tidak kebuka', 'web tidak kebuka',
            'gabisa akses web', 'gabisa buka web', 'tidak dapat membuka situs',
            'gagal akses situs', 'situs tidak terbuka',
            'halaman gagal dibuka', 'link tidak bisa dibuka', 'url tidak bisa dibuka',
            'web tidak terbuka', 'website tidak terbuka'
        ],
        'groups': [
            ['site', 'cant', 'reached'], ['tidak', 'bisa', 'akses'],
            ['tidak', 'bisa', 'buka'], ['tidak', 'dapat', 'jangkau'],
            ['gagal', 'membuka'], ['susah', 'masuk'], ['halaman', 'tidak', 'buka'],
            ['website', 'tidak', 'buka'], ['web', 'tidak', 'buka']
        ],
        'keywords': []
    },

    'G14': {
        'label_awam': 'Website gagal terhubung ke database',
        'phrases': [
            'error establishing database connection', 'establishing a database connection',
            'establishing database connection', 'database connection error',
            'database connection failed', 'error koneksi database',
            'koneksi database gagal', 'gagal koneksi database',
            'gagal connect database', 'gagal konek database',
            'tidak bisa connect database', 'tidak bisa konek database',
            'tidak dapat connect database', 'tidak dapat konek database',
            'database tidak terhubung', 'database gagal terhubung',
            'database error', 'db error', 'mysql error', 'sql error',
            'koneksi mysql gagal', 'gagal konek mysql', 'koneksi sql gagal',
            'koneksi database bermasalah', 'database bermasalah',
            'mysql bermasalah', 'database down', 'database tidak jalan',
            'database tidak aktif', 'server database mati',
            'website tidak bisa ambil data database',
            'web tidak bisa ambil data database', 'gagal mengambil data dari database',
            'tidak bisa mengambil data database', 'gagal terhubung ke database',
            'koneksi db gagal', 'db tidak konek', 'database tidak konek',
            'cannot connect to database', 'cant connect to database',
            'could not connect to database', 'failed to connect database',
            'failed to connect to database'
        ],
        'groups': [
            ['database', 'connection'], ['koneksi', 'database'],
            ['mysql', 'error'], ['sql', 'error'], ['database', 'error'],
            ['database', 'bermasalah'], ['database', 'tidak', 'terhubung'],
            ['gagal', 'terhubung', 'database'], ['tidak', 'bisa', 'connect', 'database'],
            ['failed', 'connect', 'database']
        ],
        'keywords': []
    },

    'G15': {
        'label_awam': 'Akses halaman ditolak atau tidak punya izin',
        'phrases': [
            'server forbidden', '403 forbidden', 'http 403', 'error 403',
            'status 403', 'kode 403', 'access forbidden', 'forbidden access',
            'website forbidden', 'web forbidden', 'page forbidden', 'muncul forbidden',
            'akses dilarang', 'akses ditolak', 'akses halaman ditolak',
            'hak akses ditolak', 'akses tidak diizinkan', 'tidak punya izin akses',
            'tidak memiliki izin akses', 'tidak boleh mengakses halaman',
            'dilarang mengakses halaman', 'halaman tidak diizinkan',
            'tidak bisa masuk karena forbidden', 'permission denied',
            'permission bermasalah', 'server menolak akses',
            'halaman diblokir oleh permission', 'forbidden 403', '403 error'
        ],
        'groups': [
            ['server', 'forbidden'], ['access', 'forbidden'],
            ['akses', 'ditolak'], ['akses', 'dilarang'],
            ['tidak', 'punya', 'izin'], ['permission', 'denied'],
            ['403', 'forbidden']
        ],
        'keywords': ['403', 'forbidden']
    }
}


# =====================================================================
# KONFIGURASI DETEKSI LEBIH AKURAT
# =====================================================================
# Bobot dibuat agar frasa error asli lebih kuat daripada keyword tunggal.
# Ini tetap berbasis leksikon, tetapi hasilnya lebih tahan terhadap typo dan
# kalimat ambigu.
MATCH_WEIGHTS = {
    'phrase': 1.00,   # frasa kuat: "internal server error", "connection timeout"
    'group': 0.75,    # kombinasi kata: "tidak" + "bisa" + "buka"
    'keyword': 0.55,  # keyword unik: "500", "403", "ssl"
    'fuzzy': 0.42     # typo ringan: "forbiden" -> "forbidden"
}

# Ambang minimal sebuah gejala dianggap terdeteksi.
SYMPTOM_DETECTION_THRESHOLD = 0.55

# Ambang fuzzy matching. Makin tinggi makin ketat.
FUZZY_THRESHOLD = 0.86

# Kata yang tidak boleh jadi bukti fuzzy karena terlalu umum.
FUZZY_IGNORE_WORDS = {
    'web', 'website', 'page', 'halaman', 'server', 'error', 'masalah',
    'tidak', 'bisa', 'dapat', 'gagal', 'muncul', 'ada', 'saya', 'ini',
    'itu', 'dan', 'atau', 'yang', 'di', 'ke', 'dari', 'akses'
}

# Kata/frasa yang berarti user sedang menyangkal sebuah gejala.
# Contoh: "bukan error 500, cuma halaman putih" -> G3 tidak boleh aktif.
NEGATION_SINGLE_WORDS = {'bukan', 'tanpa'}
NEGATION_MULTI_PHRASES = {
    'tidak ada', 'tidak muncul', 'bukan karena', 'bukan masalah',
    'bukan error', 'ga ada', 'gak ada', 'nggak ada'
}

# Fuzzy keyword dibuat eksplisit agar typo umum tetap terbaca, tetapi tidak
# semua kata dalam frasa dijadikan target fuzzy.
FUZZY_KEYWORDS = {
    'G1': ['ping', 'rto', 'unreachable'],
    'G2': ['blank', 'putih', 'kosong'],
    'G3': ['internal', '500'],
    'G4': ['unavailable', '503', 'overload'],
    'G5': ['timeout', 'lambat', 'loading'],
    'G6': ['404', 'nxdomain'],
    'G7': ['sebagian', 'berantakan', 'asset', 'css', 'javascript', 'layout'],
    'G8': ['clock', 'jam', 'tanggal', 'waktu'],
    'G9': ['connect', 'terhubung'],
    'G10': ['phishing', 'malware', 'malicious', 'virus', 'scam'],
    'G11': ['ssl', 'certificate', 'sertifikat', 'private', 'privacy'],
    'G12': ['refused', 'ditolak'],
    'G13': ['reached', 'jangkau', 'buka'],
    'G14': ['database', 'mysql', 'sql'],
    'G15': ['403', 'forbidden', 'permission']
}

def confidence_label(score: float) -> str:
    if score >= 1.10:
        return 'Tinggi'
    if score >= 0.70:
        return 'Sedang'
    return 'Rendah'


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _find_phrase_positions(text_normalized: str, phrase: str):
    """Cari posisi frasa dalam teks normalisasi berdasarkan token index."""
    phrase_norm = normalize_text(phrase)
    if not phrase_norm:
        return []

    text_tokens = text_normalized.split()
    phrase_tokens = phrase_norm.split()
    if not phrase_tokens:
        return []

    positions = []
    n = len(phrase_tokens)
    for i in range(0, len(text_tokens) - n + 1):
        if text_tokens[i:i+n] == phrase_tokens:
            positions.append((i, i + n - 1))
    return positions


def _is_negated(tokens, start_index: int) -> bool:
    """Cek apakah match didahului penyangkalan dalam radius dekat."""
    window_start = max(0, start_index - 4)
    before_tokens = tokens[window_start:start_index]
    before_text = ' '.join(before_tokens)

    if any(word in before_tokens for word in NEGATION_SINGLE_WORDS):
        return True
    if any(phrase in before_text for phrase in NEGATION_MULTI_PHRASES):
        return True
    return False


def _keyword_positions(tokens, keyword: str):
    keyword_norm = normalize_text(keyword)
    stemmed_kw = stemmer.stem(keyword_norm)
    positions = []
    for i, token in enumerate(tokens):
        if token == keyword_norm or stemmer.stem(token) == stemmed_kw:
            positions.append(i)
    return positions


def _add_evidence(evidence, evidence_type: str, label: str, weight: float, negated: bool = False):
    evidence.append({
        'type': evidence_type,
        'label': label,
        'weight': 0 if negated else weight,
        'negated': negated,
        'text': f"{evidence_type}: {label}" + (' (diabaikan karena negasi)' if negated else '')
    })

# ===============================
# PREPROCESSING DAN DETEKSI GEJALA
# ===============================
def normalize_text(text: str) -> str:
    text = text.lower()

    # Normalisasi apostrof dan variasi umum dari pesan browser
    text = text.replace("can't", "cant").replace("can’t", "cant")
    text = text.replace("cannot", "cant")

    # Hilangkan simbol, tetapi pertahankan underscore untuk error seperti err_connection_refused
    text = re.sub(r'[^a-z0-9\s_]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # Normalisasi slang / bahasa awam per kata
    words = []
    for word in text.split():
        words.extend(SLANG_REPLACEMENTS.get(word, word).split())

    text = ' '.join(words)
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
    }


def _contains_group(group, token_set, stem_set):
    for word in group:
        normalized_word = normalize_text(word)
        stemmed_word = stemmer.stem(normalized_word)
        if normalized_word not in token_set and stemmed_word not in stem_set:
            return False
    return True


def _group_start_index(group, tokens):
    indexes = []
    for word in group:
        normalized_word = normalize_text(word)
        stemmed_word = stemmer.stem(normalized_word)
        found_index = None
        for i, token in enumerate(tokens):
            if token == normalized_word or stemmer.stem(token) == stemmed_word:
                found_index = i
                break
        if found_index is not None:
            indexes.append(found_index)
    return min(indexes) if indexes else 0


def detect_symptoms(preprocess):
    text_normalized = preprocess['normalized']
    tokens = preprocess['tokens']
    token_set = set(preprocess['tokens'])
    stem_set = set(preprocess['tokens_stemmed_all'])

    detected = {}

    for symptom_id, pattern in SYMPTOM_PATTERNS.items():
        evidence = []

        # 1. Exact phrase matching: paling kuat.
        for phrase in pattern.get('phrases', []):
            positions = _find_phrase_positions(text_normalized, phrase)
            for start, _end in positions:
                negated = _is_negated(tokens, start)
                _add_evidence(evidence, 'frasa', phrase, MATCH_WEIGHTS['phrase'], negated)

        # 2. Group matching: beberapa kata harus muncul bersama.
        for group in pattern.get('groups', []):
            if _contains_group(group, token_set, stem_set):
                start = _group_start_index(group, tokens)
                negated = _is_negated(tokens, start)
                _add_evidence(evidence, 'kombinasi kata', ' + '.join(group), MATCH_WEIGHTS['group'], negated)

        # 3. Keyword unik/kuat: bobot lebih rendah dari frasa.
        for keyword in pattern.get('keywords', []):
            positions = _keyword_positions(tokens, keyword)
            for pos in positions:
                negated = _is_negated(tokens, pos)
                _add_evidence(evidence, 'keyword', keyword, MATCH_WEIGHTS['keyword'], negated)

        # 4. Fuzzy matching: untuk typo ringan, tetap pakai leksikon.
        for token_index, token in enumerate(tokens):
            if len(token) < 4 or token in FUZZY_IGNORE_WORDS:
                continue
            for target in FUZZY_KEYWORDS.get(symptom_id, []):
                target_norm = normalize_text(target)
                if len(target_norm) < 4 or target_norm in FUZZY_IGNORE_WORDS:
                    continue
                ratio = _similarity(token, target_norm)
                if ratio >= FUZZY_THRESHOLD and token != target_norm:
                    negated = _is_negated(tokens, token_index)
                    _add_evidence(
                        evidence,
                        'fuzzy',
                        f"{token} ≈ {target_norm} ({round(ratio * 100)}%)",
                        MATCH_WEIGHTS['fuzzy'],
                        negated
                    )

        # Hilangkan evidence duplikat berdasarkan teks.
        unique_evidence = []
        seen = set()
        for item in evidence:
            key = (item['type'], item['label'], item['negated'])
            if key not in seen:
                seen.add(key)
                unique_evidence.append(item)

        score = sum(item['weight'] for item in unique_evidence)
        accepted = score >= SYMPTOM_DETECTION_THRESHOLD

        if accepted:
            confidence_percent = min(100, round((score / 1.75) * 100))
            detected[symptom_id] = {
                'id': symptom_id,
                'text': GEJALA_MAP.get(symptom_id, symptom_id),
                'labelAwam': pattern.get('label_awam', GEJALA_MAP.get(symptom_id, symptom_id)),
                'matchedBy': [item['text'] for item in unique_evidence if not item['negated']],
                'ignoredByNegation': [item['text'] for item in unique_evidence if item['negated']],
                'confidenceScore': round(min(1.0, score / 1.75), 3),
                'confidencePercent': confidence_percent,
                'confidenceLabel': confidence_label(score)
            }

    return detected

# ===============================
# INFERENCE ENGINE BERBASIS RULE + TINGKAT KECOCOKAN
# ===============================
def diagnose_from_symptoms(selected_symptoms, symptom_confidence=None):
    selected_set = set(selected_symptoms)
    symptom_confidence = symptom_confidence or {}
    results = []

    for rule in RULES:
        matched = [g for g in rule['gejala'] if g in selected_set]
        if not matched:
            continue

        # Jika input berasal dari NLP, gejala dengan bukti kuat memberi nilai lebih tinggi.
        # Jika input manual, default confidence = 1.0.
        weighted_match = sum(symptom_confidence.get(g, 1.0) for g in matched)
        skor = weighted_match / len(rule['gejala'])
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
            'matchedDetail': [{'id': g, 'text': GEJALA_MAP.get(g, g)} for g in matched],
            'skor': skor,
            'pct': pct,
            'certaintyLabel': certainty_label(pct),
            'reason': f"{len(matched)} dari {len(rule['gejala'])} gejala pada rule {rule['kategori']} terpenuhi. Nilai disesuaikan dengan kekuatan bukti leksikon."
        })

    results.sort(key=lambda x: (x['skor'], len(x['matched'])), reverse=True)
    return results

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
        'detectionMethod': 'weighted_lexicon_fuzzy_negation'
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
            'detectedSymptoms': []
        })

    symptom_confidence = {g: detected_map[g].get('confidenceScore', 1.0) for g in detected_symptoms}
    results = diagnose_from_symptoms(detected_symptoms, symptom_confidence)
    if not results:
        return jsonify({
            'showWarning': True,
            'results': None,
            'preprocessing': preprocess,
            'detectedSymptoms': list(detected_map.values())
        })

    return jsonify({
        'showWarning': False,
        'preprocessing': preprocess,
        'detectedSymptoms': [detected_map[g] for g in detected_symptoms],
        'results': results,
        'mainResult': results[0],
        'alternativeResults': results[1:],
        'detectionMethod': 'weighted_lexicon_fuzzy_negation'
    })


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
