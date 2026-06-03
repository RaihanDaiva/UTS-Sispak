import re
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
# KAMUS KNOWLEDGE ENGINEER
# phrases  = frasa kuat, dicek langsung dari kalimat normalisasi
# groups   = beberapa kata yang harus muncul bersama, cocok untuk bahasa natural
# keywords = kata unik/kuat. Hindari kata terlalu umum seperti "server" atau "error" sendirian
# =====================================================================
SYMPTOM_PATTERNS = {
    'G1': {
        'phrases': ['tidak bisa di ping', 'tidak dapat di ping', 'gagal ping', 'request timed out'],
        'groups': [['tidak', 'bisa', 'ping'], ['gagal', 'ping']],
        'keywords': ['ping', 'rto']
    },
    'G2': {
        'phrases': ['website blank', 'halaman blank', 'halaman putih', 'layar putih', 'page blank', 'blank putih'],
        'groups': [['website', 'blank'], ['halaman', 'putih'], ['layar', 'kosong']],
        'keywords': ['blank', 'putih', 'kosong']
    },
    'G3': {
        'phrases': ['internal server error', '500 internal server error', 'http 500', 'error 500'],
        'groups': [['internal', 'server', 'error']],
        'keywords': ['500']
    },
    'G4': {
        'phrases': ['service unavailable', '503 service unavailable', 'http 503', 'error 503'],
        'groups': [['service', 'unavailable']],
        'keywords': ['503']
    },
    'G5': {
        'phrases': ['connection timeout', 'request timeout', 'koneksi timeout', 'waktu koneksi habis', 'loading lama'],
        'groups': [['connection', 'timeout'], ['request', 'timeout'], ['koneksi', 'timeout'], ['website', 'lambat']],
        'keywords': ['timeout', 'lambat', 'lelet']
    },
    'G6': {
        'phrases': ['server not found', '404 not found', 'not found', 'dns not found', 'dns_probe_finished_nxdomain'],
        'groups': [['server', 'not', 'found'], ['not', 'found']],
        'keywords': ['404', 'nxdomain']
    },
    'G7': {
        'phrases': ['data tidak sempurna', 'data tidak lengkap', 'halaman tidak lengkap', 'asset tidak load', 'gambar tidak muncul', 'css tidak load', 'javascript tidak load'],
        'groups': [['data', 'tidak', 'lengkap'], ['data', 'tidak', 'sempurna'], ['asset', 'tidak', 'load'], ['gambar', 'tidak', 'muncul']],
        'keywords': ['sebagian', 'corrupt']
    },
    'G8': {
        'phrases': ['your clock is behind', 'clock is behind', 'jam tidak sesuai', 'tanggal tidak sesuai', 'waktu komputer salah'],
        'groups': [['clock', 'behind'], ['jam', 'salah'], ['tanggal', 'salah'], ['waktu', 'salah']],
        'keywords': []
    },
    'G9': {
        'phrases': ['unable to connect', 'tidak bisa connect', 'tidak bisa konek', 'gagal koneksi', 'gagal terhubung'],
        'groups': [['unable', 'connect'], ['gagal', 'koneksi'], ['gagal', 'hubung'], ['tidak', 'bisa', 'connect'], ['tidak', 'bisa', 'konek']],
        'keywords': []
    },
    'G10': {
        'phrases': ['phishing warning', 'malicious content warning', 'konten berbahaya', 'peringatan phishing', 'peringatan malware', 'situs berbahaya'],
        'groups': [['peringatan', 'phishing'], ['peringatan', 'malware'], ['situs', 'bahaya']],
        'keywords': ['phishing', 'malware', 'scam', 'virus']
    },
    'G11': {
        'phrases': ['your connection is not private', 'connection is not private', 'koneksi tidak private', 'koneksi tidak aman', 'sertifikat ssl bermasalah', 'ssl error', 'certificate error'],
        'groups': [['connection', 'not', 'private'], ['koneksi', 'tidak', 'aman'], ['ssl', 'error'], ['sertifikat', 'ssl']],
        'keywords': []
    },
    'G12': {
        'phrases': ['network connection refused', 'connection refused', 'err_connection_refused', 'koneksi ditolak', 'akses ditolak jaringan'],
        'groups': [['connection', 'refused'], ['koneksi', 'tolak']],
        'keywords': ['refused']
    },
    'G13': {
        'phrases': ["the site can't be reached", 'the site cant be reached', 'site cant be reached', 'situs tidak dapat dijangkau', 'website tidak bisa dibuka', 'website tidak dapat dibuka', 'tidak bisa akses website'],
        'groups': [['site', 'cant', 'reached'], ['tidak', 'bisa', 'akses'], ['tidak', 'bisa', 'buka'], ['tidak', 'dapat', 'jangkau']],
        'keywords': []
    },
    'G14': {
        'phrases': ['error establishing database connection', 'establishing a database connection', 'database connection error', 'koneksi database gagal', 'tidak bisa konek database', 'tidak bisa connect database', 'mysql error', 'sql error'],
        'groups': [['database', 'connection'], ['koneksi', 'database'], ['mysql', 'error'], ['sql', 'error'], ['db', 'error']],
        'keywords': []
    },
    'G15': {
        'phrases': ['server forbidden', '403 forbidden', 'http 403', 'error 403', 'access forbidden', 'akses dilarang', 'akses ditolak'],
        'groups': [['server', 'forbidden'], ['access', 'forbidden'], ['akses', 'tolak'], ['akses', 'larang']],
        'keywords': ['403', 'forbidden']
    }
}

# ===============================
# PREPROCESSING DAN DETEKSI GEJALA
# ===============================
def normalize_text(text: str) -> str:
    text = text.lower()
    # normalisasi beberapa variasi umum agar frasa lebih mudah dideteksi
    text = text.replace("can't", "cant").replace("can’t", "cant")
    text = text.replace("cannot", "cant")
    text = text.replace("db", "database")
    text = re.sub(r'[^a-z0-9\s_]', ' ', text)
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


def detect_symptoms(preprocess):
    text_normalized = preprocess['normalized']
    token_set = set(preprocess['tokens'])
    stem_set = set(preprocess['tokens_stemmed_all'])

    detected = {}

    for symptom_id, pattern in SYMPTOM_PATTERNS.items():
        matched_by = []

        # 1. Cek frasa kuat terlebih dahulu
        for phrase in pattern.get('phrases', []):
            normalized_phrase = normalize_text(phrase)
            if normalized_phrase and normalized_phrase in text_normalized:
                matched_by.append(f"frasa: {phrase}")

        # 2. Cek kombinasi kata yang harus muncul bersama
        for group in pattern.get('groups', []):
            if _contains_group(group, token_set, stem_set):
                matched_by.append('kombinasi kata: ' + ' + '.join(group))

        # 3. Cek keyword unik/kuat
        for keyword in pattern.get('keywords', []):
            normalized_kw = normalize_text(keyword)
            stemmed_kw = stemmer.stem(normalized_kw)
            if normalized_kw in token_set or stemmed_kw in stem_set:
                matched_by.append(f"keyword: {keyword}")

        if matched_by:
            detected[symptom_id] = {
                'id': symptom_id,
                'text': GEJALA_MAP.get(symptom_id, symptom_id),
                'matchedBy': sorted(set(matched_by))
            }

    return detected

# ===============================
# INFERENCE ENGINE BERBASIS RULE + TINGKAT KECOCOKAN
# ===============================
def diagnose_from_symptoms(selected_symptoms):
    selected_set = set(selected_symptoms)
    results = []

    for rule in RULES:
        matched = [g for g in rule['gejala'] if g in selected_set]
        if not matched:
            continue

        skor = len(matched) / len(rule['gejala'])
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
            'reason': f"{len(matched)} dari {len(rule['gejala'])} gejala pada rule {rule['kategori']} terpenuhi."
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
        'alternativeResults': results[1:]
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

    results = diagnose_from_symptoms(detected_symptoms)
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
        'alternativeResults': results[1:]
    })


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
