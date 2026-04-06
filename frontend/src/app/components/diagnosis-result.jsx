import React from 'react';
import { CheckCircle, AlertTriangle } from 'lucide-react';

export function DiagnosisResult({ diagnosis }) {
  // 1. Cek jika data kosong atau tidak ada satupun gejala yang cocok dengan aturan pakar
  if (!diagnosis || diagnosis.length === 0) {
    return (
      <div className="bg-card rounded-2xl p-8 border border-border shadow-lg">
        <div className="flex items-center gap-3 mb-6">
          <AlertTriangle className="w-8 h-8 text-yellow-500" />
          <h2 className="text-2xl">Hasil Diagnosa</h2>
        </div>
        <div className="bg-primary/5 rounded-xl p-4">
          <p className="text-foreground text-center">
            Gejala yang dipilih tidak memenuhi aturan kerusakan apapun di basis pengetahuan. Coba pilih gejala lain.
          </p>
        </div>
      </div>
    );
  }

  // 2. Lakukan mapping karena 'diagnosis' sekarang berupa Array dari hasil pencocokan rule
  return (
    <div className="space-y-6">
      {diagnosis.map((item, index) => (
        <div key={index} className="bg-card rounded-2xl p-8 border border-border shadow-lg">
          <div className="flex items-center gap-3 mb-6">
            <CheckCircle className="w-8 h-8 text-green-500" />
            {/* Tambahkan penomoran jika hasil diagnosanya lebih dari 1 */}
            <h2 className="text-2xl">Hasil Diagnosa {diagnosis.length > 1 ? `#${index + 1}` : ''}</h2>
          </div>

          <div className="space-y-6">
            {/* Jenis Kerusakan */}
            <div>
              <p className="text-sm text-muted-foreground mb-2">Jenis Kerusakan</p>
              <p className="text-xl text-foreground font-bold">{item.type}</p>
            </div>

            {/* Kode */}
            <div>
              <p className="text-sm text-muted-foreground mb-2">Kode</p>
              <span className="inline-block px-4 py-2 bg-primary text-primary-foreground rounded-lg font-mono">
                {item.code}
              </span>
            </div>

            {/* Penjelasan */}
            <div className="pt-4 border-t border-border">
              <p className="text-sm text-muted-foreground mb-2">Penjelasan</p>
              <p className="text-foreground leading-relaxed">
                {item.description}
              </p>
            </div>

            {/* Saran Solusi */}
            {item.solution && (
              <div className="bg-primary/5 rounded-xl p-4">
                <p className="text-sm text-muted-foreground mb-2">Saran Solusi</p>
                <p className="text-foreground leading-relaxed">
                  {item.solution}
                </p>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}