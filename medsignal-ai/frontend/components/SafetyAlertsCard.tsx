import type { SafetyAlert } from "@/lib/api-types";

type SafetyAlertsCardProps = {
  alerts: SafetyAlert[];
  error?: string | null;
};

export function SafetyAlertsCard({ alerts, error }: SafetyAlertsCardProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">
        Recent reporting increases
      </h2>
      <p className="mt-1 text-sm leading-6 text-slate-600">
        Signals from recent changes in reported adverse event counts. These are
        review prompts, not confirmed drug risks.
      </p>

      {error ? (
        <p className="mt-4 rounded-md bg-rose-50 px-4 py-3 text-sm font-medium text-rose-800">
          {error}
        </p>
      ) : alerts.length > 0 ? (
        <div className="mt-4 space-y-3">
          {alerts.map((alert) => (
            <article key={alert.id} className="rounded-md bg-amber-50 p-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <h3 className="font-semibold text-amber-950">
                  {alert.reaction}
                </h3>
                <span className="text-sm font-semibold text-amber-900">
                  {alert.percent_change.toFixed(2)}% change
                </span>
              </div>
              <p className="mt-2 text-sm leading-6 text-amber-950">
                {alert.message}
              </p>
              <p className="mt-3 text-xs font-medium text-amber-900">
                Baseline: {alert.baseline_count} reports | Recent:{" "}
                {alert.current_count} reports
              </p>
            </article>
          ))}
        </div>
      ) : (
        <p className="mt-4 rounded-md bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-500">
          No potential safety signals have been detected for this medication in
          the saved reported adverse event data.
        </p>
      )}
    </section>
  );
}
