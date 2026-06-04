import { useState, useRef, useEffect } from "react";
import {
  Brain,
  Send,
  User,
  Loader2,
  AlertTriangle,
  Zap,
  Sun,
  Moon,
  Menu,
  SearchCheck,
  Info,
  ListChecks,
  Wrench,
} from "lucide-react";

type Message = {
  id: string;
  role: "system" | "user";
  content: string | React.ReactNode;
};

type MatchingEvidence = {
  method: string;
  candidate: string;
  normalizedCandidate?: string;
  matched?: boolean;
  fuzzyScore?: number | null;
  threshold?: number | null;
  weight?: number;
  status?: string;
};

type FuzzyCandidate = {
  candidate: string;
  normalizedCandidate?: string;
  matchedToken?: string;
  fuzzyScore: number;
  threshold: number;
  accepted: boolean;
};

type DetectedSymptom = {
  id: string;
  text: string;
  matchedBy?: string[];
  ignoredByNegation?: string[];
  confidenceScore?: number;
  confidencePercent?: number;
  confidenceLabel?: string;
  processDetail?: {
    rawScoreBeforePercent?: number;
    minimumSymptomScore?: number;
    weights?: Record<string, number>;
    thresholds?: Record<string, number>;
    acceptedEvidence?: MatchingEvidence[];
    topFuzzyPhraseCandidates?: FuzzyCandidate[];
    topFuzzyKeywordCandidates?: FuzzyCandidate[];
  };
};

type ProcessSummary = {
  pipeline?: string[];
  weights?: Record<string, number>;
  thresholds?: Record<string, number>;
  thefuzzAvailable?: boolean;
  note?: string;
};

type DiagnosisResult = {
  kategori: string;
  userTitle?: string;
  simpleExplanation?: string;
  solutionSteps?: string[];
  gejala: string[];
  solusi: string;
  matched: string[];
  matchedDetail?: DetectedSymptom[];
  skor: number;
  pct: number;
  certaintyLabel?: "Tinggi" | "Sedang" | "Rendah" | string;
  reason?: string;
};

type DiagnoseResponse = {
  showWarning: boolean;
  results?: DiagnosisResult[] | null;
  mainResult?: DiagnosisResult;
  alternativeResults?: DiagnosisResult[];
  detectedSymptoms?: DetectedSymptom[];
  preprocessing?: {
    original: string;
    normalized: string;
    tokens: string[];
    tokens_no_stop: string[];
    tokens_stemmed: string[];
    tokens_stemmed_all: string[];
    thefuzzAvailable?: boolean;
  };
  processSummary?: ProcessSummary;
  error?: string;
};

function getCertaintyStyle(label?: string) {
  if (label === "Tinggi") {
    return "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300";
  }
  if (label === "Sedang") {
    return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300";
  }
  return "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300";
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "system",
      content: (
        <div className="space-y-2">
          <p className="font-medium">Halo! Saya adalah asisten diagnosa kerusakan website.</p>
          <p>
            Ceritakan masalah website Anda dengan bahasa biasa. Supaya hasil lebih akurat, sebutkan pesan error yang muncul.
          </p>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Contoh: <span className="font-medium">“website saya blank putih”</span>, <span className="font-medium">“muncul error database connection”</span>, atau <span className="font-medium">“website connection timeout”</span>.
          </div>
        </div>
      ),
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      setIsDarkMode(true);
    }
  }, []);

  useEffect(() => {
    if (isDarkMode) document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
  }, [isDarkMode]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const renderSymptomTags = (symptoms: DetectedSymptom[] = []) => (
    <div className="flex flex-wrap gap-1.5">
      {symptoms.map((s) => (
        <span
          key={s.id}
          title={s.matchedBy?.join(" | ")}
          className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2 py-1 rounded-md text-xs"
        >
          {s.text}
          <span className="text-gray-400 ml-1">({s.id})</span>
          {typeof s.confidencePercent === "number" && (
            <span className="text-indigo-500 dark:text-indigo-300 ml-1">{s.confidencePercent}%</span>
          )}
        </span>
      ))}
    </div>
  );

  const renderDetectionProcess = (symptoms: DetectedSymptom[] = [], summary?: ProcessSummary) => {
    if (!symptoms.length && !summary) return null;

    return (
      <details className="bg-slate-50 dark:bg-gray-800/70 rounded-xl p-3 border border-slate-200 dark:border-gray-700">
        <summary className="cursor-pointer text-xs font-bold text-gray-600 dark:text-gray-300 uppercase flex items-center gap-1">
          <SearchCheck className="w-4 h-4" /> Lihat proses deteksi NLP dan fuzzy
        </summary>

        {summary && (
          <div className="mt-3 text-xs text-gray-600 dark:text-gray-300 space-y-1">
            <p><span className="font-bold">thefuzz:</span> {summary.thefuzzAvailable ? "Aktif" : "Tidak aktif / fallback difflib"}</p>
            {summary.thresholds && (
              <p>
                <span className="font-bold">Threshold:</span> fuzzy phrase {summary.thresholds.fuzzyPhrase}, fuzzy keyword {summary.thresholds.fuzzyKeyword}, minimum gejala {summary.thresholds.minimumSymptomScore}
              </p>
            )}
            {summary.weights && (
              <p>
                <span className="font-bold">Bobot:</span> phrase {summary.weights.phrase}, group {summary.weights.group}, keyword {summary.weights.keyword}, fuzzy phrase {summary.weights.fuzzy_phrase}, fuzzy keyword {summary.weights.fuzzy_keyword}
              </p>
            )}
          </div>
        )}

        <div className="mt-3 space-y-3">
          {symptoms.map((s) => {
            const detail = s.processDetail;
            const evidence = detail?.acceptedEvidence || [];
            const fuzzyPhrases = detail?.topFuzzyPhraseCandidates || [];
            const fuzzyKeywords = detail?.topFuzzyKeywordCandidates || [];

            return (
              <div key={s.id} className="rounded-lg bg-white dark:bg-gray-900/60 border border-gray-200 dark:border-gray-700 p-3">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <p className="text-sm font-bold text-gray-800 dark:text-gray-100">{s.id} - {s.text}</p>
                  {typeof s.confidencePercent === "number" && (
                    <span className="text-xs px-2 py-1 rounded-md bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 font-bold">
                      {s.confidenceLabel || "Confidence"} {s.confidencePercent}%
                    </span>
                  )}
                </div>

                {typeof s.confidenceScore === "number" && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                    Skor gejala mentah: {s.confidenceScore} | Minimum diterima: {detail?.minimumSymptomScore ?? "-"}
                  </p>
                )}

                {evidence.length > 0 && (
                  <div className="mb-2">
                    <p className="text-xs font-bold text-gray-500 dark:text-gray-400 mb-1">Bukti yang diterima:</p>
                    <ul className="text-xs text-gray-600 dark:text-gray-300 space-y-1">
                      {evidence.map((ev, index) => (
                        <li key={index}>
                          • {ev.method}: <span className="font-medium">{ev.candidate}</span>
                          {typeof ev.fuzzyScore === "number" && <> | fuzzy {ev.fuzzyScore}/{ev.threshold}</>}
                          {typeof ev.weight === "number" && <> | bobot +{ev.weight}</>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {(fuzzyPhrases.length > 0 || fuzzyKeywords.length > 0) && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                    {fuzzyPhrases.length > 0 && (
                      <div className="rounded-md bg-gray-50 dark:bg-gray-800 p-2">
                        <p className="text-xs font-bold text-gray-500 dark:text-gray-400 mb-1">Top fuzzy frasa:</p>
                        <ul className="text-xs text-gray-600 dark:text-gray-300 space-y-1">
                          {fuzzyPhrases.slice(0, 3).map((f, i) => (
                            <li key={i}>
                              • {f.candidate}: {f.fuzzyScore}/{f.threshold} {f.accepted ? "✓" : "×"}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {fuzzyKeywords.length > 0 && (
                      <div className="rounded-md bg-gray-50 dark:bg-gray-800 p-2">
                        <p className="text-xs font-bold text-gray-500 dark:text-gray-400 mb-1">Top fuzzy keyword:</p>
                        <ul className="text-xs text-gray-600 dark:text-gray-300 space-y-1">
                          {fuzzyKeywords.slice(0, 3).map((f, i) => (
                            <li key={i}>
                              • {f.candidate} ≈ {f.matchedToken}: {f.fuzzyScore}/{f.threshold} {f.accepted ? "✓" : "×"}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {s.ignoredByNegation && s.ignoredByNegation.length > 0 && (
                  <p className="text-xs text-orange-600 dark:text-orange-400 mt-2">
                    Diabaikan karena negasi: {s.ignoredByNegation.join(", ")}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </details>
    );
  };

  const renderResultCard = (result: DiagnosisResult, isMain = false) => {
    const certainty = result.certaintyLabel || (result.pct >= 70 ? "Tinggi" : result.pct >= 40 ? "Sedang" : "Rendah");
    const symptomDetails = result.matchedDetail || result.matched.map((id) => ({ id, text: id }));

    return (
      <div
        key={result.kategori}
        className={`rounded-xl p-4 shadow-sm border ${
          isMain
            ? "bg-white dark:bg-gray-800 border-indigo-200 dark:border-indigo-900/40"
            : "bg-gray-50 dark:bg-gray-800/70 border-gray-200 dark:border-gray-700"
        }`}
      >
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <p className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase mb-1">
              {isMain ? "Diagnosis Utama" : "Diagnosis Alternatif"}
            </p>
            <h4 className={`${isMain ? "text-lg" : "text-base"} font-bold text-gray-900 dark:text-gray-100`}>
              {result.userTitle || result.kategori}
            </h4>
            <p className="text-xs text-gray-400 mt-0.5">Kategori teknis: {result.kategori}</p>
          </div>
          <span className={`px-2 py-1 rounded-md text-xs font-bold whitespace-nowrap ${getCertaintyStyle(certainty)}`}>
            Kemungkinan {certainty} ({result.pct}%)
          </span>
        </div>

        {result.simpleExplanation && (
          <div className="mb-3 rounded-lg bg-indigo-50 dark:bg-indigo-900/20 p-3 text-sm text-gray-700 dark:text-gray-200 leading-relaxed">
            <div className="flex items-center gap-1 font-bold mb-1 text-indigo-700 dark:text-indigo-300">
              <Info className="w-4 h-4" /> Apa artinya?
            </div>
            {result.simpleExplanation}
          </div>
        )}

        <div className="mb-3">
          <h5 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase mb-1 flex items-center gap-1">
            <SearchCheck className="w-4 h-4" /> Gejala yang terbaca
          </h5>
          {renderSymptomTags(symptomDetails)}
        </div>

        {result.solutionSteps && result.solutionSteps.length > 0 ? (
          <div className="border-t border-indigo-50 dark:border-gray-700 pt-3">
            <h5 className="text-sm font-bold text-gray-700 dark:text-gray-200 mb-2 flex items-center gap-1">
              <Wrench className="w-4 h-4 text-indigo-500 dark:text-indigo-400" /> Langkah yang disarankan:
            </h5>
            <ol className="list-decimal list-inside text-sm text-gray-600 dark:text-gray-300 leading-relaxed space-y-1">
              {result.solutionSteps.map((step, index) => (
                <li key={index}>{step}</li>
              ))}
            </ol>
          </div>
        ) : (
          <div className="border-t border-indigo-50 dark:border-gray-700 pt-3">
            <h5 className="text-sm font-bold text-gray-700 dark:text-gray-200 mb-1 flex items-center gap-1">
              <Zap className="w-4 h-4 text-indigo-500 dark:text-indigo-400" /> Solusi Perbaikan:
            </h5>
            <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">{result.solusi}</p>
          </div>
        )}

        {result.reason && (
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-3 border-t border-gray-100 dark:border-gray-700 pt-2">
            Detail sistem: {result.reason}
          </p>
        )}
      </div>
    );
  };

  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userText = inputText.trim();
    setInputText("");

    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: "user", content: userText },
    ]);

    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/nlp-diagnose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userText }),
      });

      const data: DiagnoseResponse = await response.json();
      if (data.error) throw new Error(data.error);

      let systemResponse: React.ReactNode;

      if (data.showWarning || !data.results || data.results.length === 0) {
        systemResponse = (
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 text-orange-600 dark:text-orange-400 font-medium">
              <AlertTriangle className="w-5 h-5" /> Informasi masih kurang jelas.
            </div>
            <p>
              Saya belum bisa menentukan kerusakan dari penjelasan tersebut. Coba tambahkan pesan error atau ciri yang muncul di website.
            </p>
            <div className="bg-orange-50 dark:bg-orange-900/20 rounded-xl p-3 text-sm text-gray-700 dark:text-gray-200">
              <p className="font-bold mb-1">Contoh informasi yang bisa ditambahkan:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>Apakah website blank atau halaman putih?</li>
                <li>Apakah muncul error 500, 403, 404, atau 503?</li>
                <li>Apakah ada pesan database connection?</li>
                <li>Apakah hanya terjadi di perangkat Anda?</li>
              </ul>
            </div>
          </div>
        );
      } else {
        const mainResult = data.mainResult || data.results[0];
        const alternatives = data.alternativeResults || data.results.slice(1);

        systemResponse = (
          <div className="flex flex-col gap-4">
            <p>
              Saya membaca keluhan Anda, lalu mencocokkannya dengan gejala kerusakan website yang ada di basis pengetahuan.
            </p>

            <div className="bg-gray-50 dark:bg-gray-800/70 rounded-xl p-3 border border-gray-200 dark:border-gray-700">
              <h5 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase mb-2 flex items-center gap-1">
                <ListChecks className="w-4 h-4" /> Ringkasan yang dipahami sistem
              </h5>
              <p className="text-sm text-gray-700 dark:text-gray-200 mb-2">
                Gejala yang ditemukan dari kalimat Anda:
              </p>
              {renderSymptomTags(data.detectedSymptoms || [])}
            </div>

            {renderDetectionProcess(data.detectedSymptoms || [], data.processSummary)}

            {renderResultCard(mainResult, true)}

            {alternatives.length > 0 && (
              <div className="flex flex-col gap-3">
                <h5 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase">
                  Kemungkinan Lain yang Masih Berkaitan
                </h5>
                {alternatives.slice(0, 3).map((r) => renderResultCard(r, false))}
              </div>
            )}

            {data.preprocessing && (
              <div className="bg-gray-50 dark:bg-gray-800/70 rounded-xl p-3 border border-gray-200 dark:border-gray-700">
                <h5 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase mb-2 flex items-center gap-1">
                  <SearchCheck className="w-4 h-4" /> Detail NLP
                </h5>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  Normalisasi: {data.preprocessing.normalized}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Token hasil stemming: {data.preprocessing.tokens_stemmed.join(", ") || "-"}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  thefuzz: {data.preprocessing.thefuzzAvailable ? "aktif" : "tidak aktif / fallback difflib"}
                </p>
              </div>
            )}
          </div>
        );
      }

      setMessages((prev) => [
        ...prev,
        { id: (Date.now() + 1).toString(), role: "system", content: systemResponse },
      ]);
    } catch (err: any) {
      console.error("Chat Error:", err);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "system",
          content: `Error: ${err.message || "Koneksi ke server backend gagal. Pastikan server Flask sudah berjalan."}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="h-screen w-full flex flex-col bg-white dark:bg-gray-900 transition-colors duration-200 overflow-hidden text-gray-800 dark:text-gray-100 font-sans">
      <header className="flex-shrink-0 h-14 border-b border-gray-100 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md flex items-center justify-between px-4 sm:px-6 z-10">
        <div className="flex items-center gap-3">
          <Menu className="w-5 h-5 text-gray-500 hover:text-gray-800 dark:hover:text-gray-200 cursor-pointer transition-colors sm:hidden" />
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <h1 className="text-base sm:text-lg font-semibold tracking-tight text-gray-900 dark:text-gray-100">
              Diagnosa Kerusakan Website
            </h1>
          </div>
        </div>

        <button
          onClick={() => setIsDarkMode(!isDarkMode)}
          className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 transition-colors"
          title="Toggle Theme"
        >
          {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </header>

      <main className="flex-1 overflow-y-auto w-full scroll-smooth flex flex-col items-center">
        <div className="w-full max-w-3xl flex flex-col gap-6 p-4 sm:p-6 pb-6">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-4 sm:gap-5 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
              <div className={`flex justify-center ${msg.role === "user" ? "items-center w-10" : ""}`}>
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${msg.role === "user" ? "bg-indigo-100 dark:bg-indigo-900/50" : "bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700"}`}>
                  {msg.role === "user" ? <User className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> : <Brain className="w-4 h-4 text-gray-600 dark:text-gray-300" />}
                </div>
              </div>

              <div className={`max-w-[85%] sm:max-w-prose pt-1 ${msg.role === "user" ? "text-gray-800 dark:text-gray-100" : "text-gray-800 dark:text-gray-200"}`}>
                {msg.role === "user" ? (
                  <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl px-5 py-3 inline-block ml-auto max-w-full text-[15px] leading-relaxed shadow-sm text-left">
                    {msg.content}
                  </div>
                ) : (
                  <div className="text-[15px] leading-relaxed pr-4">{msg.content}</div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-4 sm:gap-6 w-full max-w-3xl">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 flex items-center justify-center">
                <Brain className="w-4 h-4 text-gray-600 dark:text-gray-300" />
              </div>
              <div className="flex-1 pt-2 flex items-center gap-2 text-gray-500 dark:text-gray-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm font-medium">Menganalisa keluhan...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} className="h-4" />
        </div>
      </main>

      <div className="w-full bg-white dark:bg-gray-900 pt-2 pb-6 px-4 z-20 flex justify-center">
        <div className="w-full max-w-3xl relative">
          <div className="relative shadow-[0_0_15px_rgba(0,0,0,0.05)] dark:shadow-[0_0_15px_rgba(0,0,0,0.4)] rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex items-end">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ceritakan masalah website Anda, contoh: muncul error database connection..."
              className="w-full bg-transparent text-gray-800 dark:text-gray-100 text-base p-4 pr-14 focus:outline-none resize-none max-h-32 min-h-[56px] rounded-2xl leading-relaxed"
              rows={1}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isLoading}
              className="absolute right-2 bottom-2 p-2 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 transition-colors disabled:opacity-30 disabled:hover:bg-indigo-600 flex items-center justify-center"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <p className="text-center text-xs text-gray-400 mt-3">
            Sistem membaca keluhan, mendeteksi gejala, lalu memberi diagnosis dan saran perbaikan.
          </p>
        </div>
      </div>
    </div>
  );
}
