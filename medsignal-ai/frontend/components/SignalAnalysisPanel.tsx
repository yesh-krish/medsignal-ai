import type {
  SignalAnalysis,
  SignalAnalysisRun,
} from "@/lib/api-types";

type SignalAnalysisPanelProps = {
  analysis: SignalAnalysis | null;
  history: SignalAnalysisRun[];
  isAnalyzing: boolean;
  error: string | null;
  onAnalyze: () => void;
};

export function SignalAnalysisPanel({
  analysis,
  history,
  isAnalyzing,
  error,
  onAnalyze,
}: SignalAnalysisPanelProps) {
  const potentialCount =
    analysis?.results.filter((result) => result.is_potential_signal).length ?? 0;

  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-col gap-4 border-b border-slate-200 p-5 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-medium uppercase text-teal-700">
            Disproportionality analysis
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-950">
            PRR and ROR potential safety signals
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Compares reaction reporting for this medication with all openFDA
            FAERS comparator reports. Results are screening signals, not
            confirmed drug risks.
          </p>
        </div>
        <button
          type="button"
          onClick={onAnalyze}
          disabled={isAnalyzing}
          className="h-11 shrink-0 rounded-md bg-teal-700 px-4 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {isAnalyzing ? "Analyzing reports..." : "Run PRR/ROR analysis"}
        </button>
      </div>

      {error && (
        <p className="m-5 rounded-md bg-rose-50 px-4 py-3 text-sm font-medium text-rose-800">
          {error}
        </p>
      )}

      {!analysis && !error && (
        <div className="p-5">
          <p className="rounded-md bg-slate-50 px-4 py-4 text-sm leading-6 text-slate-500">
            No PRR/ROR analysis has been saved for this medication. Run the
            analysis to calculate reporting ratios and confidence intervals.
          </p>
        </div>
      )}

      {analysis && (
        <div>
          <dl className="grid gap-4 border-b border-slate-200 p-5 sm:grid-cols-2 lg:grid-cols-5">
            <Metric label="Potential signals" value={String(potentialCount)} />
            <Metric
              label="Target reports"
              value={analysis.run.target_total_reports.toLocaleString()}
            />
            <Metric
              label="Comparator reports"
              value={analysis.run.comparator_total_reports.toLocaleString()}
            />
            <Metric
              label="Thresholds"
              value={`PRR >= ${analysis.run.prr_threshold}; CI > ${analysis.run.ror_ci_lower_threshold}`}
            />
            <Metric label="Saved runs" value={String(history.length)} />
          </dl>

          <div className="divide-y divide-slate-200">
            {analysis.results.map((result) => (
              <article key={result.id} className="p-5">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <h3 className="font-semibold text-slate-950">
                        {result.reaction}
                      </h3>
                      <span
                        className={`text-xs font-semibold uppercase ${
                          result.is_potential_signal
                            ? "text-rose-700"
                            : "text-slate-500"
                        }`}
                      >
                        {result.is_potential_signal
                          ? "Potential signal"
                          : "Below threshold"}
                      </span>
                    </div>
                    <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-600">
                      {result.explanation}
                    </p>
                  </div>
                  <dl className="grid shrink-0 grid-cols-3 gap-5 text-right">
                    <Metric label="PRR" value={result.prr.toFixed(2)} />
                    <Metric label="ROR" value={result.ror.toFixed(2)} />
                    <Metric
                      label="95% CI"
                      value={`${result.ror_ci_lower.toFixed(2)}-${result.ror_ci_upper.toFixed(2)}`}
                    />
                  </dl>
                </div>
              </article>
            ))}
          </div>

          <p className="border-t border-slate-200 px-5 py-4 text-xs leading-5 text-slate-500">
            Analysis run #{analysis.run.id}, completed {" "}
            {formatTimestamp(
              analysis.run.completed_at ?? analysis.run.started_at,
            )}. Minimum report threshold: {analysis.run.minimum_reports}.
          </p>
        </div>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase text-slate-500">{label}</dt>
      <dd className="mt-1 text-sm font-semibold text-slate-950">{value}</dd>
    </div>
  );
}

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
