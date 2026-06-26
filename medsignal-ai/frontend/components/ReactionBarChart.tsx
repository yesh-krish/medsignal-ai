"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ReactionCount } from "@/lib/api-types";

type ReactionBarChartProps = {
  data: ReactionCount[];
};

export function ReactionBarChart({ data }: ReactionBarChartProps) {
  const chartData = data.slice(0, 8);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">
        Top reported reactions
      </h2>
      <p className="mt-1 text-sm text-slate-600">
        Reaction terms from reported adverse events.
      </p>
      <div className="mt-5 h-80">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 4, right: 24, bottom: 4, left: 18 }}
            >
              <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
              <XAxis type="number" allowDecimals={false} stroke="#64748b" />
              <YAxis
                type="category"
                dataKey="reaction"
                width={132}
                tick={{ fontSize: 12 }}
                stroke="#64748b"
              />
              <Tooltip />
              <Bar dataKey="count" fill="#0f766e" radius={[0, 5, 5, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChartState />
        )}
      </div>
    </section>
  );
}

function EmptyChartState() {
  return (
    <div className="flex h-full items-center justify-center rounded-md bg-slate-50 px-4 text-center text-sm leading-6 text-slate-500">
      No reported adverse events are loaded yet. Refresh data or try another
      medication.
    </div>
  );
}
