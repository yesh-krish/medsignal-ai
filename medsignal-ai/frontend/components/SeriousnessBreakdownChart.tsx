"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

type SeriousnessBreakdownChartProps = {
  seriousnessBreakdown: Record<string, number>;
};

const colors: Record<string, string> = {
  serious: "#be123c",
  not_serious: "#0f766e",
};

export function SeriousnessBreakdownChart({
  seriousnessBreakdown,
}: SeriousnessBreakdownChartProps) {
  const chartData = Object.entries(seriousnessBreakdown).map(([name, value]) => ({
    name: name === "not_serious" ? "Non-serious" : "Serious",
    key: name,
    value,
  }));

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">
        Serious vs non-serious
      </h2>
      <p className="mt-1 text-sm text-slate-600">
        Seriousness classification in reported adverse events.
      </p>
      <div className="mt-5 h-72">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                innerRadius={58}
                outerRadius={96}
                paddingAngle={3}
              >
                {chartData.map((entry) => (
                  <Cell
                    key={entry.key}
                    fill={colors[entry.key] ?? "#64748b"}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChartState />
        )}
      </div>
      <div className="mt-3 flex flex-wrap gap-3">
        {chartData.map((entry) => (
          <div key={entry.key} className="flex items-center gap-2 text-sm">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: colors[entry.key] ?? "#64748b" }}
            />
            <span className="text-slate-700">
              {entry.name}: <strong>{entry.value}</strong>
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

function EmptyChartState() {
  return (
    <div className="flex h-full items-center justify-center rounded-md bg-slate-50 px-4 text-center text-sm leading-6 text-slate-500">
      No seriousness breakdown is available yet.
    </div>
  );
}
