"use client";

import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ReactionSignalTimeline, SignalTimeline } from "@/lib/api-types";

type SignalTimelinePanelProps = {
  timeline: SignalTimeline | null;
};

const statusLabels: Record<ReactionSignalTimeline["status"], string> = {
  new: "New",
  continuing: "Continuing",
  resolved: "Resolved",
  below_threshold: "Below threshold",
};

const statusStyles: Record<ReactionSignalTimeline["status"], string> = {
  new: "bg-rose-50 text-rose-700",
  continuing: "bg-amber-50 text-amber-800",
  resolved: "bg-emerald-50 text-emerald-800",
  below_threshold: "bg-slate-100 text-slate-600",
};

export function SignalTimelinePanel({ timeline }: SignalTimelinePanelProps) {
  const [selectedReaction, setSelectedReaction] = useState<string | null>(null);
  const reactions = timeline?.reactions ?? [];
  const selected =
    reactions.find((reaction) => reaction.reaction === selectedReaction) ??
    reactions[0] ??
    null;

  const chartData = useMemo(
    () =>
      selected?.points.map((point) => ({
        run: `#${point.run_id}`,
        prr: point.prr,
        ror: point.ror,
        isPotentialSignal: point.is_potential_signal,
      })) ?? [],
    [selected],
  );

  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 p-5">
        <p className="text-sm font-medium uppercase text-teal-700">
          Historical signal tracking
        </p>
        <h2 className="mt-2 text-xl font-semibold text-slate-950">
          PRR/ROR changes across saved runs
        </h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          Tracks potential safety signals across analysis runs so newly
          detected, continuing, and resolved signals can be reviewed over time.
        </p>
      </div>

      {!timeline || timeline.run_count === 0 ? (
        <div className="p-5">
          <p className="rounded-md bg-slate-50 px-4 py-4 text-sm leading-6 text-slate-500">
            No historical signal runs are available yet. Run PRR/ROR analysis
            more than once to build a trend over time.
          </p>
        </div>
      ) : (
        <div className="grid gap-0 xl:grid-cols-[360px_1fr]">
          <div className="border-b border-slate-200 p-5 xl:border-b-0 xl:border-r">
            <div className="mb-4 flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-slate-950">
                Tracked reactions
              </p>
              <span className="text-xs font-medium text-slate-500">
                {timeline.run_count} saved runs
              </span>
            </div>
            <div className="space-y-3">
              {reactions.map((reaction) => (
                <button
                  key={reaction.reaction}
                  type="button"
                  onClick={() => setSelectedReaction(reaction.reaction)}
                  className={`w-full rounded-md border p-4 text-left transition ${
                    selected?.reaction === reaction.reaction
                      ? "border-teal-600 bg-teal-50"
                      : "border-slate-200 bg-white hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <span className="text-sm font-semibold text-slate-950">
                      {reaction.reaction}
                    </span>
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-semibold ${
                        statusStyles[reaction.status]
                      }`}
                    >
                      {statusLabels[reaction.status]}
                    </span>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-slate-500">
                    Latest PRR {reaction.latest_prr.toFixed(2)}; ROR{" "}
                    {reaction.latest_ror.toFixed(2)}
                  </p>
                </button>
              ))}
            </div>
          </div>

          <div className="p-5">
            {selected ? (
              <>
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-950">
                      {selected.reaction}
                    </h3>
                    <p className="mt-1 text-sm leading-6 text-slate-600">
                      {selected.first_detected_at
                        ? `First detected as a potential safety signal on ${formatTimestamp(selected.first_detected_at)}.`
                        : "This reaction has not crossed the potential safety signal threshold in saved runs."}
                    </p>
                  </div>
                  <span
                    className={`w-fit rounded-full px-3 py-1 text-xs font-semibold ${
                      statusStyles[selected.status]
                    }`}
                  >
                    {statusLabels[selected.status]}
                  </span>
                </div>

                <div className="mt-5 h-72">
                  {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={chartData}
                        margin={{ top: 8, right: 18, left: 0, bottom: 0 }}
                      >
                        <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                        <XAxis dataKey="run" stroke="#64748b" />
                        <YAxis stroke="#64748b" />
                        <Tooltip />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="prr"
                          name="PRR"
                          stroke="#0f766e"
                          strokeWidth={2}
                          dot={{ r: 4 }}
                        />
                        <Line
                          type="monotone"
                          dataKey="ror"
                          name="ROR"
                          stroke="#4f46e5"
                          strokeWidth={2}
                          dot={{ r: 4 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyChartState />
                  )}
                </div>
              </>
            ) : (
              <EmptyChartState />
            )}
          </div>
        </div>
      )}
    </section>
  );
}

function EmptyChartState() {
  return (
    <div className="flex h-full min-h-40 items-center justify-center rounded-md bg-slate-50 px-4 text-center text-sm leading-6 text-slate-500">
      No signal history chart is available yet.
    </div>
  );
}

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
