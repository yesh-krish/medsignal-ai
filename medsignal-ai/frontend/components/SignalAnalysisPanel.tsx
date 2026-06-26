import type {
  SignalAnalysis,
  SignalResult,
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

          <div className="space-y-5 p-5">
            {analysis.results.map((result) => (
              <ExplainableSignalCard
                key={result.id}
                result={result}
                run={analysis.run}
              />
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

function ExplainableSignalCard({
  result,
  run,
}: {
  result: SignalResult;
  run: SignalAnalysisRun;
}) {
  const targetTotal =
    result.target_with_reaction + result.target_without_reaction;
  const comparatorTotal =
    result.comparator_with_reaction + result.comparator_without_reaction;
  const targetReactionRate = safePercent(
    result.target_with_reaction,
    targetTotal,
  );
  const comparatorReactionRate = safePercent(
    result.comparator_with_reaction,
    comparatorTotal,
  );
  const thresholdChecks = [
    {
      label: `Minimum ${run.minimum_reports} reports`,
      passed: result.target_with_reaction >= run.minimum_reports,
      detail: `${result.target_with_reaction.toLocaleString()} reports mentioning this medication and reaction`,
    },
    {
      label: `PRR at least ${run.prr_threshold.toFixed(2)}`,
      passed: result.prr >= run.prr_threshold,
      detail: `PRR ${result.prr.toFixed(2)}`,
    },
    {
      label: `ROR lower bound above ${run.ror_ci_lower_threshold.toFixed(2)}`,
      passed: result.ror_ci_lower > run.ror_ci_lower_threshold,
      detail: `Lower bound ${result.ror_ci_lower.toFixed(2)}`,
    },
  ];

  return (
    <article
      className={`rounded-lg border p-5 ${
        result.is_potential_signal
          ? "border-rose-200 bg-rose-50/40"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="text-lg font-semibold text-slate-950">
              {result.reaction}
            </h3>
            <span
              className={`rounded-full px-3 py-1 text-xs font-semibold uppercase ${
                result.is_potential_signal
                  ? "bg-rose-100 text-rose-700"
                  : "bg-slate-100 text-slate-600"
              }`}
            >
              {result.is_potential_signal
                ? "Potential safety signal"
                : "Below threshold"}
            </span>
          </div>
          <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-600">
            {buildPlainEnglishInterpretation(
              result,
              targetReactionRate,
              comparatorReactionRate,
            )}
          </p>
        </div>
        <dl className="grid shrink-0 grid-cols-3 gap-4 text-left sm:text-right">
          <Metric label="PRR" value={result.prr.toFixed(2)} />
          <Metric label="ROR" value={result.ror.toFixed(2)} />
          <Metric
            label="95% CI"
            value={`${result.ror_ci_lower.toFixed(2)}-${result.ror_ci_upper.toFixed(2)}`}
          />
        </dl>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[1fr_360px]">
        <div className="overflow-hidden rounded-md border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">2x2 signal table</th>
                <th className="px-4 py-3">With reaction</th>
                <th className="px-4 py-3">Without reaction</th>
                <th className="px-4 py-3">Reaction rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              <tr>
                <td className="px-4 py-3 font-medium text-slate-950">
                  Reports mentioning this medication
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {result.target_with_reaction.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {result.target_without_reaction.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {targetReactionRate}
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-medium text-slate-950">
                  Comparator FAERS reports
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {result.comparator_with_reaction.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {result.comparator_without_reaction.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {comparatorReactionRate}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="rounded-md border border-slate-200 bg-white p-4">
          <h4 className="text-sm font-semibold text-slate-950">
            Threshold checklist
          </h4>
          <div className="mt-4 space-y-3">
            {thresholdChecks.map((check) => (
              <div key={check.label} className="flex gap-3">
                <span
                  className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                    check.passed
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {check.passed ? "Y" : "N"}
                </span>
                <div>
                  <p className="text-sm font-medium text-slate-950">
                    {check.label}
                  </p>
                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    {check.detail}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <details className="mt-5 rounded-md bg-slate-50 px-4 py-3">
        <summary className="cursor-pointer text-sm font-semibold text-slate-800">
          View generated explanation
        </summary>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          {result.explanation}
        </p>
      </details>
    </article>
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

function buildPlainEnglishInterpretation(
  result: SignalResult,
  targetReactionRate: string,
  comparatorReactionRate: string,
): string {
  const comparison =
    `${result.reaction} appears in ${targetReactionRate} of reports mentioning ` +
    `this medication and ${comparatorReactionRate} of comparator FAERS reports.`;
  if (result.is_potential_signal) {
    return (
      `${comparison} It meets the configured report-count, PRR, and ROR ` +
      "confidence-bound thresholds, so it is flagged for review as a potential safety signal."
    );
  }
  return (
    `${comparison} It does not meet every configured threshold, so it is not ` +
    "flagged as a potential safety signal in this run."
  );
}

function safePercent(numerator: number, denominator: number): string {
  if (denominator <= 0) return "0.00%";
  return `${((numerator / denominator) * 100).toFixed(2)}%`;
}

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
