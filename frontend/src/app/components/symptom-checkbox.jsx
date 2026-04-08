import React from 'react';

export function SymptomCheckbox({ code, label, checked, onChange, disabled }) {
  return (
    <label className={`flex items-start gap-3 p-4 bg-card rounded-xl border border-border hover:border-primary/50 cursor-pointer transition-all group ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        disabled={disabled && !checked}
        className="mt-0.5 w-5 h-5 rounded border-2 border-secondary text-primary focus:ring-2 focus:ring-primary/20 cursor-pointer accent-primary"
      />
      <div className="flex-1">
        <span className="inline-block px-2 py-0.5 bg-secondary/10 text-secondary rounded-md text-sm mr-2">
          {code}
        </span>
        <span className="text-foreground group-hover:text-primary transition-colors">
          {label}
        </span>
      </div>
    </label>
  );
}
