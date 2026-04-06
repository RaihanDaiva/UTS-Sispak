// Expert System untuk Troubleshooting Website
// Menggunakan Pure Forward Chaining (Rule-Based IF-THEN absolut)

// Expert System untuk Troubleshooting Website
// Pure Forward Chaining (IF-THEN tanpa perhitungan probabilitas)

export const problemDatabase = {
  P1: {
    code: 'P1',
    type: 'Network',
    symptoms: ['G1', 'G12'],
    description: 'Masalah pada koneksi jaringan',
    solution: 'Cek koneksi internet, DNS, dan firewall'
  },
  P2: {
    code: 'P2',
    type: 'Server',
    symptoms: ['G2', 'G3'],
    description: 'Masalah pada server website',
    solution: 'Periksa konfigurasi server dan log error'
  },
  P3: {
    code: 'P3',
    type: 'Database',
    symptoms: ['G3', 'G14'],
    description: 'Koneksi database bermasalah',
    solution: 'Cek konfigurasi database dan kredensial'
  },
  P4: {
    code: 'P4',
    type: 'Server',
    symptoms: ['G4', 'G6'],
    description: 'Server tidak tersedia',
    solution: 'Restart server atau cek status hosting'
  },
  P5: {
    code: 'P5',
    type: 'Network',
    symptoms: ['G5', 'G12'],
    description: 'Timeout jaringan',
    solution: 'Cek bandwidth dan koneksi jaringan'
  },
  P6: {
    code: 'P6',
    type: 'Network',
    symptoms: ['G6', 'G1'],
    description: 'Host tidak ditemukan',
    solution: 'Periksa DNS dan koneksi internet'
  },
  P7: {
    code: 'P7',
    type: 'Database',
    symptoms: ['G7', 'G2'],
    description: 'Data tidak termuat sempurna',
    solution: 'Periksa query dan koneksi database'
  },
  P8: {
    code: 'P8',
    type: 'Komputer Pengguna',
    symptoms: ['G8', 'G11'],
    description: 'Masalah pada device user',
    solution: 'Perbaiki waktu sistem dan cek sertifikat SSL'
  },
  P9: {
    code: 'P9',
    type: 'Network',
    symptoms: ['G9', 'G12'],
    description: 'Tidak dapat terhubung ke server',
    solution: 'Periksa firewall dan jaringan'
  },
  P10: {
    code: 'P10',
    type: 'Scripting',
    symptoms: ['G10', 'G11'],
    description: 'Masalah keamanan atau script',
    solution: 'Periksa script dan keamanan website'
  },
  P11: {
    code: 'P11',
    type: 'Server',
    symptoms: ['G11', 'G15'],
    description: 'Akses server ditolak',
    solution: 'Cek permission dan konfigurasi server'
  },
  P12: {
    code: 'P12',
    type: 'Network',
    symptoms: ['G12', 'G5'],
    description: 'Masalah koneksi jaringan',
    solution: 'Periksa koneksi dan timeout'
  },
  P13: {
    code: 'P13',
    type: 'Network',
    symptoms: ['G13', 'G1'],
    description: 'Website tidak dapat dijangkau',
    solution: 'Periksa DNS dan koneksi'
  },
  P14: {
    code: 'P14',
    type: 'Database',
    symptoms: ['G14', 'G3'],
    description: 'Error database',
    solution: 'Cek koneksi database dan query'
  },
  P15: {
    code: 'P15',
    type: 'Server',
    symptoms: ['G15', 'G4'],
    description: 'Server forbidden',
    solution: 'Periksa permission dan konfigurasi server'
  }
};

// Fungsi Inferensi Pure Forward Chaining
export function calculateDiagnosis(selectedSymptoms) {
  if (!selectedSymptoms || selectedSymptoms.length === 0) {
    return [];
  }

  let matchedDiagnoses = [];

  for (const problem of Object.values(problemDatabase)) {
    const matchedCount = problem.symptoms.filter(symptom =>
      selectedSymptoms.includes(symptom)
    ).length;

    // RULE AKTIF (pure forward chaining)
    const isRuleSatisfied = matchedCount === problem.symptoms.length;

    if (isRuleSatisfied) {
      matchedDiagnoses.push({
        code: problem.code,
        type: problem.type,
        description: problem.description,
        solution: problem.solution,
        matchedSymptoms: problem.symptoms,
        score: 100 // full match
      });
    }
  }

  // 🔥 Jika tidak ada yang FULL MATCH → fallback
  if (matchedDiagnoses.length === 0) {
    for (const problem of Object.values(problemDatabase)) {
      const matchedCount = problem.symptoms.filter(symptom =>
        selectedSymptoms.includes(symptom)
      ).length;

      if (matchedCount > 0) {
        matchedDiagnoses.push({
          code: problem.code,
          type: problem.type,
          description: problem.description,
          solution: problem.solution,
          matchedSymptoms: problem.symptoms,
          score: Math.round((matchedCount / problem.symptoms.length) * 100)
        });
      }
    }

    // urutkan dari yang paling cocok
    matchedDiagnoses.sort((a, b) => b.score - a.score);
  }

  return matchedDiagnoses;
}

// Daftar semua gejala dari CSV
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
  { code: "G10", label: "Phishing or Malicious Content Warnings" },
  { code: "G11", label: "Your connection is not private" },
  { code: "G12", label: "Network connection Refused" },
  { code: "G13", label: "The site can’t be reached" },
  { code: "G14", label: "Establishing a database connection" },
  { code: "G15", label: "Server Forbidden" },
  // Lengkapi sesuai data dari Excel kamu
];