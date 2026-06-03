from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Allow CORS for React frontend
CORS(app)

# Knowledge Base
GEJALA = [
    { 'id': 'G1', 'text': 'Tidak bisa di ping' },
    { 'id': 'G2', 'text': 'Website blank' },
    { 'id': 'G3', 'text': 'Internal Server Error' },
    { 'id': 'G4', 'text': 'Service Unavailable' },
    { 'id': 'G5', 'text': 'Connection Timeout' },
    { 'id': 'G6', 'text': 'Server Not Found' },
    { 'id': 'G7', 'text': 'Data tidak sempurna di load' },
    { 'id': 'G8', 'text': 'Your clock is behind' },
    { 'id': 'G9', 'text': 'Unable to connect' },
    { 'id': 'G10', 'text': 'Phishing or Malicious Content Warnings' },
    { 'id': 'G11', 'text': 'Your connection is not private' },
    { 'id': 'G12', 'text': 'Network connection Refused' },
    { 'id': 'G13', 'text': "The site can't be reached" },
    { 'id': 'G14', 'text': 'Error establishing database connection' },
    { 'id': 'G15', 'text': 'Server Forbidden' },
]

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

@app.route("/api/gejala", methods=["GET"])
def get_gejala():
    return jsonify({"gejala": GEJALA})

@app.route("/api/diagnose", methods=["POST"])
def run_diagnose():
    data = request.get_json()
    if not data or 'selectedSymptoms' not in data:
        return jsonify({"error": "Data tidak valid"}), 400
        
    selected = data['selectedSymptoms']
    
    if not selected:
        return jsonify({"error": "Pilih minimal 1 gejala terlebih dahulu."}), 400
    
    scored = []
    for r in RULES:
        matched = [g for g in r['gejala'] if g in selected]
        skor = len(matched) / len(r['gejala'])
        pct = round(skor * 100)
        scored.append({
            "kategori": r['kategori'],
            "gejala": r['gejala'],
            "solusi": r['solusi'],
            "matched": matched,
            "skor": skor,
            "pct": pct
        })
        
    # Sort descending by score
    scored.sort(key=lambda x: x['skor'], reverse=True)
    
    max_pct = scored[0]['pct'] if scored else 0
    
    if max_pct < 30:
        return jsonify({"showWarning": True, "results": None})
    
    results = [r for r in scored if len(r['matched']) > 0]
    return jsonify({"showWarning": False, "results": results})

if __name__ == "__main__":
    # Run the Flask app on port 8000 to match the frontend fetch URL
    app.run(host="127.0.0.1", port=8000, debug=True)
