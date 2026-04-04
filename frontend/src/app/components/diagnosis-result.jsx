import React from 'react';
import { CheckCircle, AlertTriangle } from 'lucide-react';

export function DiagnosisResult({ diagnosis }) {
  if (!diagnosis) return null;

  const confidenceColor = 
    diagnosis.confidence >= 80 ? 'bg-green-500' :
    diagnosis.confidence >= 60 ? 'bg-yellow-500' :
    'bg-orange-500';

  const confidenceTextColor = 
    diagnosis.confidence >= 80 ? 'text-green-600' :
    diagnosis.confidence >= 60 ? 'text-yellow-600' :
    'text-orange-600';

  return (
    <div className="bg-card rounded-2xl p-8 border border-border shadow-lg">
      <div className="flex items-center gap-3 mb-6">
        {diagnosis.confidence >= 70 ? (
          <CheckCircle className="w-8 h-8 text-green-500" />
        ) : (
          <AlertTriangle className="w-8 h-8 text-yellow-500" />
        )}
        <h2 className="text-2xl">Hasil Diagnosa</h2>
      </div>

      <div className="space-y-6">
        {/* Jenis Kerusakan */}
        <div>
          <p className="text-sm text-muted-foreground mb-2">Jenis Kerusakan</p>
          <p className="text-xl text-foreground">{diagnosis.type}</p>
        </div>

        {/* Kode */}
        <div>
          <p className="text-sm text-muted-foreground mb-2">Kode</p>
          <span className="inline-block px-4 py-2 bg-primary text-primary-foreground rounded-lg">
            {diagnosis.code}
          </span>
        </div>

        {/* Tingkat Kepercayaan */}
        <div>
          <p className="text-sm text-muted-foreground mb-3">Tingkat Kepercayaan</p>
          <div className="space-y-2">
            <div className="w-full bg-muted rounded-full h-4 overflow-hidden">
              <div 
                className={`h-full ${confidenceColor} transition-all duration-500 ease-out rounded-full`}
                style={{ width: `${diagnosis.confidence}%` }}
              />
            </div>
            <p className={`${confidenceTextColor}`}>
              {diagnosis.confidence.toFixed(1)}%
            </p>
          </div>
        </div>

        {/* Penjelasan */}
        <div className="pt-4 border-t border-border">
          <p className="text-sm text-muted-foreground mb-2">Penjelasan</p>
          <p className="text-foreground leading-relaxed">
            {diagnosis.description}
          </p>
        </div>

        {/* Saran Solusi */}
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
