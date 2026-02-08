export default function HomePage() {
  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <p className="text-sm uppercase tracking-widest text-slate-400">Kickoff</p>
        <h2 className="text-2xl font-semibold text-white">SignalSentry is warming up</h2>
        <p className="mt-2 text-slate-300">
          Backend ingestion, anomaly detection, and root-cause engines are live. Upcoming commits will light up this
          dashboard with realtime incidents, service scorecards, and guided remediation steps.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {[1, 2, 3, 4].map((index) => (
          <div key={index} className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
            <p className="text-sm text-slate-400">Widget placeholder {index}</p>
            <p className="text-lg text-slate-200">Coming soon</p>
          </div>
        ))}
      </div>
    </section>
  );
}
