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

type ReportsOverTimeChartProps = {
  reportsByYear: Record<string, number>;
};

export function ReportsOverTimeChart({
  reportsByYear,
}: ReportsOverTimeChartProps) {
  const chartData = Object.entries(reportsByYear).map(([year, reports]) => ({
    year,
    reports,
  }));

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">Reports by year</h2>
      <p className="mt-1 text-sm text-slate-600">
        Counts from reports mentioning this medication.
      </p>
      <div className="mt-5 h-72">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 8, right: 18, left: 0 }}>
              <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
              <XAxis dataKey="year" stroke="#64748b" />
              <YAxis allowDecimals={false} stroke="#64748b" />
              <Tooltip />
              <Bar dataKey="reports" fill="#2563eb" radius={[5, 5, 0, 0]} />
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
    <div className="flex h-full items-center justify-center rounded-md bg-slate-50 text-sm text-slate-500">
      No report timeline loaded.
    </div>
  );
}
