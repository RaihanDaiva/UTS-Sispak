// Expert System untuk Troubleshooting Website
// Menggunakan Forward Chaining dengan Certainty Factor

export const problemDatabase = {
  P1: {
    code: 'P1',
    type: 'Masalah Server Down',
    symptoms: ['G1', 'G3', 'G4', 'G5'],
    description: 'Server mengalami gangguan atau tidak merespons. Ini bisa disebabkan oleh server yang down, overload, atau maintenance.',
    solution: 'Cek status server melalui hosting provider, periksa log server, atau hubungi administrator server untuk memastikan service berjalan dengan baik.'
  },
  P2: {
    code: 'P2',
    type: 'Masalah DNS / Domain',
    symptoms: ['G6', 'G13'],
    description: 'Domain tidak dapat ditemukan atau DNS tidak dapat melakukan resolving. Kemungkinan masalah pada konfigurasi DNS atau domain expired.',
    solution: 'Periksa konfigurasi DNS di domain registrar, pastikan nameserver sudah benar, dan cek apakah domain masih aktif (belum expired).'
  },
  P3: {
    code: 'P3',
    type: 'Masalah SSL / Sertifikat Keamanan',
    symptoms: ['G8', 'G11'],
    description: 'Sertifikat SSL bermasalah, expired, atau tidak valid. Ini menyebabkan browser menampilkan peringatan keamanan.',
    solution: 'Perbarui sertifikat SSL, pastikan waktu sistem sudah benar, dan gunakan sertifikat dari Certificate Authority yang terpercaya (seperti Let\'s Encrypt).'
  },
  P4: {
    code: 'P4',
    type: 'Masalah Jaringan Client',
    symptoms: ['G5', 'G9', 'G12'],
    description: 'Koneksi jaringan dari sisi client bermasalah. Bisa karena masalah ISP, firewall, atau konfigurasi jaringan lokal.',
    solution: 'Cek koneksi internet, restart router/modem, nonaktifkan firewall atau VPN sementara, dan coba akses dari jaringan lain untuk memastikan masalahnya.'
  },
  P5: {
    code: 'P5',
    type: 'Masalah Database',
    symptoms: ['G14', 'G3'],
    description: 'Database tidak dapat diakses atau mengalami error. Kemungkinan credential salah, database server down, atau database corrupt.',
    solution: 'Periksa konfigurasi database di file konfigurasi aplikasi, cek status database server, dan pastikan user database memiliki hak akses yang benar.'
  },
  P6: {
    code: 'P6',
    type: 'Masalah Hak Akses / Permission',
    symptoms: ['G15'],
    description: 'Server menolak akses ke resource tertentu karena masalah permission atau IP blocking.',
    solution: 'Periksa file .htaccess atau konfigurasi server, pastikan IP tidak terblokir, dan cek permission file/folder di server (biasanya 755 untuk folder, 644 untuk file).'
  },
  P7: {
    code: 'P7',
    type: 'Masalah Loading Resource',
    symptoms: ['G7', 'G2'],
    description: 'Resource seperti CSS, JavaScript, atau gambar tidak ter-load dengan sempurna. Bisa disebabkan oleh koneksi lambat atau file rusak.',
    solution: 'Clear cache browser, periksa console browser untuk error, cek apakah semua file resource ada di server, dan pastikan path file sudah benar.'
  },
  P8: {
    code: 'P8',
    type: 'Masalah Keamanan / Phishing',
    symptoms: ['G10'],
    description: 'Website terdeteksi sebagai phishing atau berbahaya oleh browser. Kemungkinan website ter-hack atau masuk blacklist.',
    solution: 'Scan website dari malware, periksa file-file mencurigakan di server, ganti semua password, dan submit request untuk review ke Google Safe Browsing.'
  },
  P9: {
    code: 'P9',
    type: 'Masalah Website Blank/Error',
    symptoms: ['G2', 'G3'],
    description: 'Website menampilkan halaman kosong atau error 500. Kemungkinan ada error di kode PHP/aplikasi atau memory limit tercapai.',
    solution: 'Aktifkan error reporting untuk melihat error detail, periksa log error, cek memory limit di php.ini, dan debug kode aplikasi.'
  }
};

// Hitung tingkat kepercayaan menggunakan Certainty Factor
export function calculateDiagnosis(selectedSymptoms) {
  if (selectedSymptoms.length === 0) {
    return null;
  }

  let bestMatch = null;
  let highestScore = 0;

  // Iterasi setiap masalah
  for (const [key, problem] of Object.entries(problemDatabase)) {
    // Hitung berapa banyak gejala yang cocok
    const matchedSymptoms = problem.symptoms.filter(s => 
      selectedSymptoms.includes(s)
    );
    
    if (matchedSymptoms.length === 0) continue;

    // Calculate Certainty Factor
    // CF = (jumlah gejala cocok / total gejala masalah) * 100
    let baseCF = (matchedSymptoms.length / problem.symptoms.length) * 100;
    
    // Bonus jika semua gejala dari masalah terpenuhi
    if (matchedSymptoms.length === problem.symptoms.length) {
      baseCF = Math.min(95, baseCF + 10);
    }
    
    // Penalti jika ada terlalu banyak gejala tambahan yang tidak relevan
    const extraSymptoms = selectedSymptoms.filter(s => 
      !problem.symptoms.includes(s)
    );
    
    if (extraSymptoms.length > 0) {
      const penalty = Math.min(20, extraSymptoms.length * 5);
      baseCF = Math.max(30, baseCF - penalty);
    }

    // Update best match jika score lebih tinggi
    if (baseCF > highestScore) {
      highestScore = baseCF;
      bestMatch = {
        ...problem,
        confidence: baseCF,
        matchedSymptoms: matchedSymptoms.length,
        totalSymptoms: problem.symptoms.length
      };
    }
  }

  return bestMatch;
}

// Daftar semua gejala
export const symptoms = [
  { code: "G1", label: "Tidak bisa di ping" },
  { code: "G2", label: "Website blank" },
  { code: "G3", label: "Internal Server Error" },
  { code: "G4", label: "Service Unavailable" },
  { code: "G5", label: "Connection Timeout" },
  { code: "G6", label: "Server Not Found" },
  { code: "G7", label: "Data tidak sempurna di load" },
  { code: "G8", label: "Your clock is behind" },
  { code: "G9", label: "Unable to connect" },
  { code: "G10", label: "Phishing warning" },
  { code: "G11", label: "Connection is not private" },
  { code: "G12", label: "Network connection refused" },
  { code: "G13", label: "Site can't be reached" },
  { code: "G14", label: "Database connection error" },
  { code: "G15", label: "Server Forbidden" }
];
