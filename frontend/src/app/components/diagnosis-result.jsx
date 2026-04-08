import React from 'react';
import { CheckCircle, AlertTriangle } from 'lucide-react';

export function DiagnosisResult({ diagnosis }) {
  // 1. Jika tidak ada hasil sama sekali
  if (!diagnosis) {
    return (
      <div className="bg-card rounded-2xl p-8 border border-border shadow-lg">
        <div className="flex items-center gap-3 mb-6">
          <AlertTriangle className="w-8 h-8 text-yellow-500" />
          <h2 className="text-2xl">Hasil Diagnosa</h2>
        </div>
        <div className="bg-primary/5 rounded-xl p-4">
          <p className="text-foreground text-center">
            Gejala yang dipilih tidak memenuhi aturan kerusakan apapun di basis pengetahuan.
          </p>
        </div>
      </div>
    );
  }

  // 2. Tampilkan 1 hasil (object langsung)
  return (
    <div className="bg-card rounded-2xl p-8 border border-border shadow-lg">
      <div className="flex items-center gap-3 mb-6">
        <CheckCircle className="w-8 h-8 text-green-500" />
        <h2 className="text-2xl">Hasil Diagnosa</h2>
      </div>

      <div className="space-y-6">
        {/* Jenis Kerusakan */}
        <div>
          <p className="text-sm text-muted-foreground mb-2">Jenis Kerusakan</p>
          <p className="text-xl text-foreground font-bold">{diagnosis.type}</p>
        </div>

        {/* Kode */}
        <div>
          <p className="text-sm text-muted-foreground mb-2">Kode</p>
          <span className="inline-block px-4 py-2 bg-primary text-primary-foreground rounded-lg font-mono">
            {diagnosis.code}
          </span>
        </div>

        {/* Penjelasan */}
        <div className="pt-4 border-t border-border">
          <p className="text-sm text-muted-foreground mb-2">Penjelasan</p>
          <p className="text-foreground leading-relaxed">
            {diagnosis.description}
          </p>
        </div>

        {/* Solusi */}
        {diagnosis.solution && (
          <div className="bg-primary/5 rounded-xl p-4">
            <p className="text-sm text-muted-foreground mb-2">Saran Solusi</p>
            <p className="text-foreground leading-relaxed">
              {diagnosis.solution}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}