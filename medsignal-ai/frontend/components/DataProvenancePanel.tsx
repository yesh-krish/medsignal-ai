import type { IngestionRun } from "@/lib/api-types";

type DataProvenancePanelProps = {
  run: IngestionRun | null;
};

export function DataProvenancePanel({ run }: DataProvenancePanelProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">Data provenance</h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            Audit details for the saved reported adverse event sample.
          </p>
        </div>
        {run && (
          <span
            className={`text-sm font-semibold ${
              run.status === "succeeded"
                ? "text-emerald-700"
                : run.status === "failed"
                  ? "text-rose-700"
                  : "text-amber-700"
            }`}
          >
            {run.status}
          </span>
        )}
      </div>

      {run ? (
        <dl className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <ProvenanceItem label="Source" value={run.source} />
          <ProvenanceItem
            label="Last refreshed"
            value={formatTimestamp(run.completed_at ?? run.started_at)}
          />
          <ProvenanceItem
            label="Reports fetched"
            value={`${run.fetched_reports} / ${run.requested_reports}`}
          />
          <ProvenanceItem
            label="Reaction rows saved"
            value={run.saved_reaction_rows.toLocaleString()}
          />
          <ProvenanceItem
            label="Duplicates removed"
            value={run.duplicate_reports_skipped.toLocaleString()}
          />
          <ProvenanceItem
            label="Source updated"
            value={run.source_last_updated ?? "Not provided"}
          />
        </dl>
      ) : (
        <p className="mt-4 rounded-md bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-500">
          No ingestion run has been recorded for this medication yet.
        </p>
      )}
    </section>
  );
}

function ProvenanceItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase text-slate-500">{label}</dt>
      <dd className="mt-1 break-words text-sm font-semibold text-slate-950">
        {value}
      </dd>
    </div>
  );
}

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
