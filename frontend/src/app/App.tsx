import { useState, useEffect } from "react";
import {
  Brain,
  Zap,
  RotateCcw,
  CheckCircle2,
  Server,
  AlertTriangle,
  Loader2,
} from "lucide-react";

// Data structures fetched from backend

type DiagnosisResult = {
  kategori: string;
  gejala: string[];
  solusi: string;
  matched: string[];
  skor: number;
  pct: number;
};

export default function App() {
  const [gejala, setGejala] = useState<{id: string, text: string}[]>([]);
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([]);
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);

  useEffect(() => {
    fetch("http://localhost:8000/api/gejala")
      .then((res) => res.json())
      .then((data) => setGejala(data.gejala))
      .catch((err) => console.error("Failed to fetch gejala", err));
  }, []);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [diagnosisResults, setDiagnosisResults] = useState<
    DiagnosisResult[] | null
  >(null);
  const [showWarning, setShowWarning] = useState(false);

  const toggleSymptom = (id: string) => {
    setSelectedSymptoms((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id],
    );
  };

  const resetAll = () => {
    setSelectedSymptoms([]);
    setCurrentStep(1);
    setDiagnosisResults(null);
    setShowWarning(false);
  };

  const runDiagnosis = async () => {
    if (selectedSymptoms.length === 0) {
      alert("Pilih minimal 1 gejala terlebih dahulu.");
      return;
    }

    setCurrentStep(2);
    setIsAnalyzing(true);

    try {
      const response = await fetch("http://localhost:8000/api/diagnose", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ selectedSymptoms }),
      });
      const data = await response.json();
      
      if (data.error) {
        alert(data.error);
        setIsAnalyzing(false);
        setCurrentStep(1);
        return;
      }

      setShowWarning(data.showWarning);
      setDiagnosisResults(data.results);
      setIsAnalyzing(false);
      setCurrentStep(3);
    } catch (err) {
      console.error("Failed to diagnose", err);
      alert("Koneksi ke server backend gagal. Pastikan server Python berjalan di http://localhost:8000");
      setIsAnalyzing(false);
      setCurrentStep(1);
    }
  };

  const getColor = (pct: number) => {
    if (pct >= 60) return { bg: "bg-green-500", text: "text-green-600" };
    if (pct >= 30) return { bg: "bg-orange-500", text: "text-orange-600" };
    return { bg: "bg-red-500", text: "text-red-600" };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <header className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl mb-6 shadow-lg">
            <Brain className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-4">
            Website Diagnostic AI
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-3">
            Masukkan gejala yang terdeteksi, sistem akan menganalisis
            menggunakan metode forward chaining
          </p>
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium">
            <Server className="w-4 h-4" />
            Forward Chaining Expert System
          </span>
        </header>

        {/* Step Indicator */}
        <div className="mb-12">
          <div className="flex items-center justify-center gap-4">
            {[
              { num: 1, label: "Select Symptoms" },
              { num: 2, label: "Analyze" },
              { num: 3, label: "Results" },
            ].map((step, idx) => (
              <div key={step.num} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center font-semibold transition-all duration-300 ${
                      currentStep >= step.num
                        ? "bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg scale-110"
                        : "bg-gray-200 text-gray-500"
                    }`}
                  >
                    {currentStep > step.num ? (
                      <CheckCircle2 className="w-6 h-6" />
                    ) : (
                      step.num
                    )}
                  </div>
                  <span
                    className={`mt-2 text-sm font-medium ${
                      currentStep >= step.num
                        ? "text-indigo-600"
                        : "text-gray-500"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
                {idx < 2 && (
                  <div
                    className={`w-16 sm:w-24 h-1 rounded-full mx-2 transition-all duration-300 ${
                      currentStep > step.num
                        ? "bg-gradient-to-r from-indigo-500 to-purple-600"
                        : "bg-gray-200"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Symptoms Section */}
        <div className="bg-white rounded-3xl shadow-xl p-6 sm:p-8 mb-8 border border-gray-100">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
            <h2 className="text-xl font-semibold text-gray-800">
              Knowledge Base — Pilih Gejala yang Terdeteksi
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {gejala.map((g) => (
              <button
                key={g.id}
                onClick={() => toggleSymptom(g.id)}
                className={`group relative p-4 rounded-xl border-2 transition-all duration-200 text-left ${
                  selectedSymptoms.includes(g.id)
                    ? "border-indigo-500 bg-gradient-to-br from-indigo-50 to-purple-50 shadow-md scale-105"
                    : "border-gray-200 bg-white hover:border-indigo-300 hover:shadow-sm"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                      selectedSymptoms.includes(g.id)
                        ? "border-indigo-500 bg-indigo-500"
                        : "border-gray-300 group-hover:border-indigo-400"
                    }`}
                  >
                    {selectedSymptoms.includes(g.id) && (
                      <CheckCircle2 className="w-4 h-4 text-white" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-bold text-indigo-600 mb-1">
                      {g.id}
                    </div>
                    <div className="text-sm text-gray-700 leading-snug">
                      {g.text}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <button
              onClick={runDiagnosis}
              disabled={isAnalyzing}
              className="flex-1 sm:flex-initial sm:px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Zap className="w-5 h-5" />
              Run Diagnosis
            </button>
            <button
              onClick={resetAll}
              className="px-6 py-4 border-2 border-gray-300 hover:border-gray-400 text-gray-700 font-medium rounded-xl transition-all duration-200 flex items-center gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </button>
            <span className="text-sm text-gray-600 font-medium">
              {selectedSymptoms.length} gejala dipilih
            </span>
          </div>
        </div>

        {/* Loading State */}
        {isAnalyzing && (
          <div className="bg-white rounded-3xl shadow-xl p-12 mb-8 text-center border border-gray-100">
            <div className="flex flex-col items-center gap-4">
              <div className="relative">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
                  <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
                </div>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-800 mb-2">
                  Analyzing symptoms...
                </h3>
                <p className="text-gray-600">
                  Running forward chaining inference engine
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Results Section */}
        {!isAnalyzing && currentStep === 3 && (
          <>
            {showWarning && (
              <div className="bg-orange-50 border-2 border-orange-300 rounded-2xl p-6 mb-8 flex items-start gap-4">
                <AlertTriangle className="w-6 h-6 text-orange-600 flex-shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold text-orange-900 mb-1">
                    Diagnosa tidak cukup kuat
                  </h3>
                  <p className="text-orange-800">
                    Skor tertinggi hanya {diagnosisResults?.[0]?.pct || 0}%.
                    Silakan pilih lebih banyak gejala untuk hasil yang lebih
                    akurat.
                  </p>
                </div>
              </div>
            )}

            {diagnosisResults && diagnosisResults.length > 0 && (
              <>
                {/* Inference Engine Trace */}
                <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-6 mb-8 border border-gray-200">
                  <h3 className="font-semibold text-gray-800 mb-3 text-sm">
                    Proses Inference Engine (Forward Chaining):
                  </h3>
                  <div className="space-y-2 text-sm text-gray-700 leading-relaxed">
                    <p>
                      Fakta awal:{" "}
                      <strong className="text-gray-900">
                        {selectedSymptoms.join(", ")}
                      </strong>
                    </p>
                    <p>
                      Rule aktif (minimal 1 gejala terpenuhi):{" "}
                      <strong className="text-gray-900">
                        {diagnosisResults.map((r) => r.kategori).join(", ")}
                      </strong>
                    </p>
                    <p className="text-gray-600 text-xs">
                      Evaluasi skor = gejala cocok / total gejala per rule →
                      sistem memilih skor tertinggi sebagai diagnosa utama.
                    </p>
                  </div>
                </div>

                {/* Main Diagnosis */}
                <div className="mb-8">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
                    <h2 className="text-xl font-semibold text-gray-800">
                      Diagnosa Utama
                    </h2>
                  </div>

                  {diagnosisResults
                    .filter((r) => r.pct === diagnosisResults[0].pct)
                    .map((result, idx) => {
                      const color = getColor(result.pct);
                      return (
                        <div
                          key={idx}
                          className="bg-white rounded-3xl shadow-2xl border-2 border-indigo-500 p-8 mb-6 relative overflow-hidden"
                        >
                          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-purple-600"></div>
                          <span className="absolute top-6 right-6 px-4 py-1.5 bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-xs font-bold rounded-full shadow-lg">
                            MAIN DIAGNOSIS
                          </span>

                          <h3 className="text-3xl font-bold text-gray-900 mb-6">
                            {result.kategori}
                          </h3>

                          <div className="flex items-end gap-4 mb-4">
                            <div className={`text-5xl font-bold ${color.text}`}>
                              {result.pct}%
                            </div>
                            <div className="text-sm text-gray-600 pb-2 leading-tight">
                              Tingkat kecocokan
                              <br />
                              <strong className="text-gray-800">
                                {result.matched.length} dari{" "}
                                {result.gejala.length}
                              </strong>{" "}
                              gejala terpenuhi
                            </div>
                          </div>

                          <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden mb-6">
                            <div
                              className={`h-full ${color.bg} transition-all duration-1000 ease-out rounded-full`}
                              style={{ width: `${result.pct}%` }}
                            ></div>
                          </div>

                          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-5 mb-6">
                            <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">
                              Explanation Facility — Gejala yang Cocok
                            </h4>
                            <div className="flex flex-wrap gap-2">
                              {result.gejala.map((gid) => {
                                const g = gejala.find((x) => x.id === gid);
                                const isMatched = result.matched.includes(gid);
                                return (
                                  <span
                                    key={gid}
                                    title={g?.text}
                                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                                      isMatched
                                        ? "bg-green-100 text-green-700 border-2 border-green-300"
                                        : "bg-gray-200 text-gray-500 border-2 border-gray-300"
                                    }`}
                                  >
                                    {gid}
                                    {isMatched && " ✓"}
                                  </span>
                                );
                              })}
                            </div>
                          </div>

                          <div className="border-t-2 border-gray-200 pt-6">
                            <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                              <Zap className="w-5 h-5 text-indigo-600" />
                              Solusi / Langkah Perbaikan:
                            </h4>
                            <p className="text-gray-700 leading-relaxed">
                              {result.solusi}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                </div>

                {/* Alternative Diagnoses */}
                {diagnosisResults.filter((r) => r.pct < diagnosisResults[0].pct)
                  .length > 0 && (
                  <>
                    <hr className="border-t-2 border-gray-200 my-8" />
                    <div className="mb-8">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-2 h-2 rounded-full bg-gray-400"></div>
                        <h2 className="text-xl font-semibold text-gray-800">
                          Diagnosa Alternatif (berdasarkan ranking)
                        </h2>
                      </div>

                      <div className="grid grid-cols-1 gap-4">
                        {diagnosisResults
                          .filter((r) => r.pct < diagnosisResults[0].pct)
                          .map((result, idx) => {
                            const color = getColor(result.pct);
                            return (
                              <div
                                key={idx}
                                className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 hover:shadow-xl transition-all duration-200"
                              >
                                <div className="flex items-center justify-between mb-4">
                                  <div className="flex items-center gap-3">
                                    <h3 className="text-lg font-semibold text-gray-900">
                                      {result.kategori}
                                    </h3>
                                    <span className="px-2.5 py-1 bg-gray-200 text-gray-700 text-xs font-bold rounded-full">
                                      #{idx + 2}
                                    </span>
                                  </div>
                                  <div
                                    className={`text-2xl font-bold ${color.text}`}
                                  >
                                    {result.pct}%
                                  </div>
                                </div>

                                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
                                  <div
                                    className={`h-full ${color.bg} transition-all duration-1000 ease-out`}
                                    style={{ width: `${result.pct}%` }}
                                  ></div>
                                </div>

                                <div className="bg-gray-50 rounded-xl p-4 mb-4">
                                  <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                                    Gejala yang cocok
                                  </h4>
                                  <div className="flex flex-wrap gap-2">
                                    {result.gejala.map((gid) => {
                                      const g = gejala.find(
                                        (x) => x.id === gid,
                                      );
                                      const isMatched =
                                        result.matched.includes(gid);
                                      return (
                                        <span
                                          key={gid}
                                          title={g?.text}
                                          className={`px-2.5 py-1 rounded-md text-xs font-semibold ${
                                            isMatched
                                              ? "bg-green-100 text-green-700"
                                              : "bg-gray-200 text-gray-500"
                                          }`}
                                        >
                                          {gid}
                                          {isMatched && " ✓"}
                                        </span>
                                      );
                                    })}
                                  </div>
                                </div>

                                <p className="text-sm text-gray-600 leading-relaxed">
                                  {result.solusi}
                                </p>
                              </div>
                            );
                          })}
                      </div>
                    </div>
                  </>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
