// ===============================
// DAFTAR GEJALA
// ===============================
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
  { code: "G15", label: "Server Forbidden" }
];

// ===============================
// RULE BERDASARKAN PAKAR
// ===============================
export const categoryRules = [
  {
    type: "Network",
    symptoms: ["G1", "G5", "G6", "G9", "G12", "G13"]
  },
  {
    type: "Server",
    symptoms: ["G2", "G3", "G4", "G5", "G6", "G11", "G13", "G14", "G15"]
  },
  {
    type: "Database",
    symptoms: ["G7", "G9", "G14"]
  },
  {
    type: "Komputer Pengguna",
    symptoms: ["G8", "G10", "G11"]
  },
  {
    type: "Scripting",
    symptoms: ["G2", "G3", "G10", "G15"]
  },
  {
    type: "Frontend",
    symptoms: ["G2", "G7", "G13"]
  }
];

// ===============================
// FORWARD CHAINING (SINGLE RESULT)
// ===============================
export function calculateDiagnosis(selectedSymptoms) {
  if (!selectedSymptoms || selectedSymptoms.length === 0) {
    return null;
  }

  let bestMatch = null;
  let highestMatch = 0;

  for (const rule of categoryRules) {
    // hitung jumlah gejala yang cocok
    const matchCount = rule.symptoms.filter(symptom =>
      selectedSymptoms.includes(symptom)
    ).length;

    // simpan yang paling banyak cocok
    if (matchCount > highestMatch) {
      highestMatch = matchCount;
      bestMatch = rule;
    }
  }

  // jika tidak ada yang cocok sama sekali
  if (highestMatch === 0) {
    return null;
  }

  // return 1 hasil saja
  return {
    type: bestMatch.type,
    matchedSymptoms: bestMatch.symptoms.filter(symptom =>
      selectedSymptoms.includes(symptom)
    ),
    totalMatched: highestMatch
  };
} 