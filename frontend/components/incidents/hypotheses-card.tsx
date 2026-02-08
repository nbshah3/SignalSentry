import type { RootCauseResponse } from '@/types/api';

export function HypothesesCard({ analysis }: { analysis: RootCauseResponse }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="border-b border-slate-800 px-6 py-4">
        <h3 className="text-lg font-semibold text-white">Root-cause hypotheses</h3>
        <p className="text-sm text-slate-400">Correlation and keyword evidence gathered from the backend.</p>
      </div>
      <ul className="divide-y divide-slate-800">
        {analysis.hypotheses.map((hypothesis) => (
          <li key={hypothesis.title} className="px-6 py-4">
            <div className="flex items-center justify-between">
              <p className="text-xl font-semibold text-white">{hypothesis.title}</p>
              <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">
                Confidence {hypothesis.confidence}%
              </span>
            </div>
            <ul className="mt-2 space-y-1 text-sm text-slate-300">
              {hypothesis.evidence.map((evidence, index) => (
                <li key={index} className="text-slate-400">
                  <span className="font-semibold uppercase text-slate-500">{evidence.type}:</span> {evidence.detail}
                </li>
              ))}
            </ul>
          </li>
        ))}
        {!analysis.hypotheses.length && (
          <li className="px-6 py-6 text-center text-sm text-slate-500">No hypotheses generated.</li>
        )}
      </ul>
    </div>
  );
}
