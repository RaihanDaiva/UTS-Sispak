import React, { useState } from 'react';
import { SymptomCheckbox } from './components/symptom-checkbox';
import { DiagnosisResult } from './components/diagnosis-result';
import { symptoms, calculateDiagnosis } from './utils/expert-system';
import { Activity, RotateCcw } from 'lucide-react';

export default function App() {
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([]);
  const [diagnosis, setDiagnosis] = useState<any>(null);
  const [showResult, setShowResult] = useState(false);

  const handleSymptomChange = (code: string) => {
    setSelectedSymptoms(prev => {
      if (prev.includes(code)) {
        return prev.filter(s => s !== code);
      } else {
        return [...prev, code];
      }
    });
  };

  const handleDiagnose = () => {
    const result = calculateDiagnosis(selectedSymptoms);
    setDiagnosis(result);
    setShowResult(true);
    
    // Scroll to result
    setTimeout(() => {
      document.getElementById('result-section')?.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
      });
    }, 100);
  };

  const handleReset = () => {
    setSelectedSymptoms([]);
    setDiagnosis(null);
    setShowResult(false);
  };

  // Split symptoms into two columns
  const midPoint = Math.ceil(symptoms.length / 2);
  const leftColumn = symptoms.slice(0, midPoint);
  const rightColumn = symptoms.slice(midPoint);

  return (
    <div className="min-h-screen bg-background" style={{ fontFamily: 'Inter, sans-serif' }}>
      {/* Header */}
      <header className="bg-card border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center gap-3 mb-2">
            <Activity className="w-10 h-10 text-primary" />
            <h1 className="text-3xl">Diagnosa Masalah Website</h1>
          </div>
          <p className="text-muted-foreground">
            Pilih gejala yang terjadi pada website Anda
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        {/* Input Gejala Section */}
        <section className="mb-12">
          <div className="mb-6">
            <h3 className="text-xl mb-2">Daftar Gejala</h3>
            <p className="text-muted-foreground text-sm">
              Pilih satu atau lebih gejala yang sesuai dengan masalah yang Anda alami
            </p>
          </div>

          {/* 2 Column Layout */}
          <div className="grid md:grid-cols-2 gap-4 mb-8">
            {/* Left Column */}
            <div className="space-y-3">
              {leftColumn.map(symptom => (
                <SymptomCheckbox
                  key={symptom.code}
                  code={symptom.code}
                  label={symptom.label}
                  checked={selectedSymptoms.includes(symptom.code)}
                  onChange={() => handleSymptomChange(symptom.code)}
                />
              ))}
            </div>

            {/* Right Column */}
            <div className="space-y-3">
              {rightColumn.map(symptom => (
                <SymptomCheckbox
                  key={symptom.code}
                  code={symptom.code}
                  label={symptom.label}
                  checked={selectedSymptoms.includes(symptom.code)}
                  onChange={() => handleSymptomChange(symptom.code)}
                />
              ))}
            </div>
          </div>

          {/* Selected Count */}
          <div className="mb-6 p-4 bg-primary/5 rounded-xl border border-primary/20">
            <p className="text-sm text-foreground">
              <span className="text-primary">
                {selectedSymptoms.length}
              </span>
              {' '}gejala terpilih
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-4">
            <button
              onClick={handleDiagnose}
              disabled={selectedSymptoms.length === 0}
              className="px-8 py-3 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-md hover:shadow-lg"
            >
              <Activity className="w-5 h-5" />
              Diagnosa Sekarang
            </button>

            <button
              onClick={handleReset}
              className="px-8 py-3 bg-secondary text-secondary-foreground rounded-xl hover:bg-secondary/90 transition-all flex items-center gap-2"
            >
              <RotateCcw className="w-5 h-5" />
              Reset
            </button>
          </div>
        </section>

        {/* Hasil Diagnosa Section */}
        {showResult && (
          <section id="result-section" className="animate-fade-in">
            {diagnosis ? (
              <DiagnosisResult diagnosis={diagnosis} />
            ) : (
              <div className="bg-card rounded-2xl p-8 border border-border">
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-muted rounded-full mb-4">
                    <Activity className="w-8 h-8 text-muted-foreground" />
                  </div>
                  <h3 className="text-xl mb-2">Tidak Ada Diagnosa</h3>
                  <p className="text-muted-foreground">
                    Gejala yang dipilih tidak cocok dengan database masalah yang ada. 
                    Silakan pilih gejala lain atau hubungi teknisi profesional.
                  </p>
                </div>
              </div>
            )}
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-card border-t border-border mt-20">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <p className="text-center text-sm text-muted-foreground">
            Sistem Pakar Troubleshooting Website • Forward Chaining Expert System
          </p>
        </div>
      </footer>

      <style>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fade-in {
          animation: fade-in 0.4s ease-out;
        }
      `}</style>
    </div>
  );
}