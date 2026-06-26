"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { Drug, DrugComparison } from "@/lib/api-types";

type Side = "left" | "right";

type SelectionState = {
  query: string;
  drug: Drug | null;
  isSearching: boolean;
  error: string | null;
};

const initialSelection: SelectionState = {
  query: "",
  drug: null,
  isSearching: false,
  error: null,
};

const sideLabels: Record<Side, string> = {
  left: "Medication A",
  right: "Medication B",
};

export default function MedicationComparisonPage() {
  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
  const [left, setLeft] = useState<SelectionState>(initialSelection);
  const [right, setRight] = useState<SelectionState>(initialSelection);
  const [comparison, setComparison] = useState<DrugComparison | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);

  const canCompare = Boolean(left.drug && right.drug && left.drug.id !== right.drug.id);

  async function searchMedication(side: Side) {
    const current = side === "left" ? left : right;
    const setCurrent = side === "left" ? setLeft : setRight;
    const cleanedQuery = current.query.trim();
    if (!cleanedQuery) {
      setCurrent((state) => ({ ...state, error: "Enter a medication name." }));
      return;
    }

    setCurrent((state) => ({ ...state, isSearching: true, error: null }));
    setComparison(null);
    setComparisonError(null);

    try {
      const response = await fetch(
        `${backendUrl}/api/drugs/search?query=${encodeURIComponent(cleanedQuery)}`,
      );
      if (response.status === 404) {
        throw new Error("No matching medication found.");
      }
      if (response.status === 504) {
        throw new Error("RxNorm timed out. Try again in a moment.");
      }
      if (!response.ok) {
        throw new Error("Medication search is unavailable right now.");
      }
      const drug = (await response.json()) as Drug;
      setCurrent((state) => ({
        ...state,
        drug,
        query: drug.normalized_name ?? state.query,
        isSearching: false,
        error: null,
      }));
    } catch (caughtError) {
      setCurrent((state) => ({
        ...state,
        drug: null,
        isSearching: false,
        error:
          caughtError instanceof Error
            ? caughtError.message
            : "Medication search failed.",
      }));
    }
  }

  async function compareMedications() {
    if (!left.drug || !right.drug) return;

    setIsComparing(true);
    setComparisonError(null);
    try {
      const response = await fetch(
        `${backendUrl}/api/drugs/compare?left_id=${left.drug.id}&right_id=${right.drug.id}`,
      );
      if (response.status === 504) {
        throw new Error("openFDA comparison timed out. Try again shortly.");
      }
      if (response.status === 422) {
        throw new Error("Choose two different medications to compare.");
      }
      if (!response.ok) {
        throw new Error("Medication comparison could not be loaded.");
      }
      setComparison((await response.json()) as DrugComparison);
    } catch (caughtError) {
      setComparison(null);
      setComparisonError(
        caughtError instanceof Error
          ? caughtError.message
          : "Medication comparison failed.",
      );
    } finally {
      setIsComparing(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f7faf9] px-6 py-6 text-slate-950">
      <div className="mx-auto max-w-7xl">
        <header className="border-b border-slate-200 pb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <Link href="/medsignal-ai" className="text-sm font-medium text-teal-700">
                Back to MedSignal AI
              </Link>
              <p className="mt-5 text-sm font-medium uppercase text-teal-700">
                Medication comparison
              </p>
              <h1 className="mt-2 text-4xl font-semibold tracking-normal">
                Compare reported adverse event patterns
              </h1>
            </div>
          </div>
          <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-600">
            Compare recent openFDA report counts and FDA label sections side by
            side. These counts are influenced by reporting behavior and cannot
            establish which medication is safer.
          </p>
        </header>

        <section className="mt-6 grid gap-5 lg:grid-cols-[1fr_1fr_auto]">
          <MedicationSearchCard
            side="left"
            state={left}
            onChange={(query) => setLeft((state) => ({ ...state, query }))}
            onSearch={() => searchMedication("left")}
          />
          <MedicationSearchCard
            side="right"
            state={right}
            onChange={(query) => setRight((state) => ({ ...state, query }))}
            onSearch={() => searchMedication("right")}
          />
          <div className="flex items-end">
            <button
              type="button"
              onClick={compareMedications}
              disabled={!canCompare || isComparing}
              className="h-12 w-full rounded-md bg-slate-950 px-5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400 lg:w-44"
            >
              {isComparing ? "Comparing" : "Compare"}
            </button>
          </div>
        </section>

        {comparisonError && (
          <div className="mt-6 rounded-lg border border-rose-200 bg-rose-50 p-5 text-sm font-medium text-rose-800 shadow-sm">
            {comparisonError}
          </div>
        )}

        {!comparison && !comparisonError && (
          <div className="mt-6 rounded-lg border border-slate-200 bg-white p-6 text-sm leading-6 text-slate-600 shadow-sm">
            Search and select two medications, then run a comparison to see
            recent reports mentioning each medication, common reported reactions,
            seriousness distribution, and FDA label section coverage.
          </div>
        )}

        {comparison && <ComparisonDashboard comparison={comparison} />}
      </div>
    </main>
  );
}

function MedicationSearchCard({
  side,
  state,
  onChange,
  onSearch,
}: {
  side: Side;
  state: SelectionState;
  onChange: (query: string) => void;
  onSearch: () => void;
}) {
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        onSearch();
      }}
      className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
    >
      <label className="block text-sm font-medium text-slate-700">
        {sideLabels[side]}
      </label>
      <div className="mt-3 flex gap-3">
        <input
          value={state.query}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Search medications"
          className="h-12 min-w-0 flex-1 rounded-md border border-slate-300 bg-white px-4 text-base outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
        />
        <button
          type="submit"
          disabled={state.isSearching}
          className="h-12 rounded-md bg-teal-700 px-4 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {state.isSearching ? "Searching" : "Search"}
        </button>
      </div>
      <div className="mt-3 min-h-6">
        {state.drug && (
          <p className="text-sm font-medium text-emerald-700">
            Selected {state.drug.normalized_name ?? state.drug.input_name}
          </p>
        )}
        {state.error && (
          <p className="text-sm font-medium text-rose-700">{state.error}</p>
        )}
      </div>
    </form>
  );
}

function ComparisonDashboard({ comparison }: { comparison: DrugComparison }) {
  return (
    <div className="mt-6 space-y-6">
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-950 shadow-sm">
        {comparison.disclaimer}
      </div>

      <section className="grid gap-5 lg:grid-cols-2">
        <DrugSummaryCard side="Medication A" item={comparison.left} />
        <DrugSummaryCard side="Medication B" item={comparison.right} />
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <ReportVolumeChart comparison={comparison} />
        <SeriousnessComparisonChart comparison={comparison} />
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <SharedReactionsTable comparison={comparison} />
        <LabelComparisonCard comparison={comparison} />
      </section>
    </div>
  );
}

function DrugSummaryCard({
  side,
  item,
}: {
  side: string;
  item: DrugComparison["left"];
}) {
  const drugName = item.drug.normalized_name ?? item.drug.input_name;
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-medium uppercase text-slate-500">{side}</p>
      <h2 className="mt-2 text-2xl font-semibold text-slate-950">{drugName}</h2>
      <dl className="mt-5 grid gap-3 sm:grid-cols-3">
        <Metric label="Total reports" value={item.trends.total_reports.toLocaleString()} />
        <Metric label="RxCUI" value={item.drug.rxcui ?? "Unknown"} />
        <Metric label="TTY" value={item.drug.tty ?? "Unknown"} />
      </dl>
      <Link
        href={`/medsignal-ai/drugs/${item.drug.id}`}
        className="mt-5 inline-flex text-sm font-medium text-teal-700 transition hover:text-teal-900"
      >
        Open dashboard
      </Link>
    </article>
  );
}

function ReportVolumeChart({ comparison }: { comparison: DrugComparison }) {
  const data = useMemo(() => {
    const years = Array.from(
      new Set([
        ...Object.keys(comparison.left.trends.reports_by_year),
        ...Object.keys(comparison.right.trends.reports_by_year),
      ]),
    ).sort();
    return years.map((year) => ({
      year,
      left: comparison.left.trends.reports_by_year[year] ?? 0,
      right: comparison.right.trends.reports_by_year[year] ?? 0,
    }));
  }, [comparison]);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">
        Recent report volume by year
      </h2>
      <p className="mt-1 text-sm text-slate-600">
        Counts from reports mentioning each medication.
      </p>
      <div className="mt-5 h-80">
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 8, right: 18, left: 0 }}>
              <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
              <XAxis dataKey="year" stroke="#64748b" />
              <YAxis allowDecimals={false} stroke="#64748b" />
              <Tooltip />
              <Legend />
              <Bar
                name={comparison.left.drug.normalized_name ?? "Medication A"}
                dataKey="left"
                fill="#0f766e"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                name={comparison.right.drug.normalized_name ?? "Medication B"}
                dataKey="right"
                fill="#4f46e5"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState text="No yearly comparison data is available yet." />
        )}
      </div>
    </section>
  );
}

function SeriousnessComparisonChart({ comparison }: { comparison: DrugComparison }) {
  const data = [
    {
      name: comparison.left.drug.normalized_name ?? "Medication A",
      serious: comparison.left.trends.seriousness_breakdown.serious ?? 0,
      nonSerious: comparison.left.trends.seriousness_breakdown.not_serious ?? 0,
    },
    {
      name: comparison.right.drug.normalized_name ?? "Medication B",
      serious: comparison.right.trends.seriousness_breakdown.serious ?? 0,
      nonSerious: comparison.right.trends.seriousness_breakdown.not_serious ?? 0,
    },
  ];
  const pieData = data.flatMap((item) => [
    { name: `${item.name} serious`, value: item.serious, color: "#be123c" },
    { name: `${item.name} non-serious`, value: item.nonSerious, color: "#0f766e" },
  ]).filter((item) => item.value > 0);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">
        Serious vs non-serious
      </h2>
      <p className="mt-1 text-sm text-slate-600">
        Seriousness classification in reported adverse events.
      </p>
      <div className="mt-5 h-80">
        {pieData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                innerRadius={58}
                outerRadius={105}
                paddingAngle={2}
              >
                {pieData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState text="No seriousness comparison data is available yet." />
        )}
      </div>
      <div className="mt-3 grid gap-2 text-sm text-slate-700">
        {data.map((item) => (
          <p key={item.name}>
            <span className="font-medium text-slate-950">{item.name}:</span>{" "}
            {item.serious.toLocaleString()} serious,{" "}
            {item.nonSerious.toLocaleString()} non-serious
          </p>
        ))}
      </div>
    </section>
  );
}

function SharedReactionsTable({ comparison }: { comparison: DrugComparison }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">
        Common reported reactions
      </h2>
      <p className="mt-1 text-sm text-slate-600">
        Reaction terms appearing in both top reported adverse event lists.
      </p>
      <div className="mt-5 overflow-hidden rounded-md border border-slate-200">
        {comparison.shared_top_reported_reactions.length > 0 ? (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Reaction</th>
                <th className="px-4 py-3">Medication A</th>
                <th className="px-4 py-3">Medication B</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {comparison.shared_top_reported_reactions.map((reaction) => (
                <tr key={reaction.reaction}>
                  <td className="px-4 py-3 font-medium text-slate-950">
                    {reaction.reaction}
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    {reaction.left_count.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    {reaction.right_count.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <EmptyState text="No shared top reported reactions were found." />
        )}
      </div>
    </section>
  );
}

function LabelComparisonCard({ comparison }: { comparison: DrugComparison }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">
        FDA label section differences
      </h2>
      <p className="mt-1 text-sm text-slate-600">
        Availability of key FDA label sections returned by openFDA.
      </p>
      <div className="mt-5 space-y-3">
        {comparison.label_section_comparison.map((section) => (
          <div
            key={section.section}
            className="rounded-md border border-slate-200 p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <h3 className="text-sm font-semibold text-slate-950">
                {section.section}
              </h3>
              <span className="text-xs font-medium text-slate-500">
                {section.left_count} vs {section.right_count} entries
              </span>
            </div>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              <AvailabilityPill
                label="Medication A"
                available={section.left_available}
              />
              <AvailabilityPill
                label="Medication B"
                available={section.right_available}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function AvailabilityPill({
  label,
  available,
}: {
  label: string;
  available: boolean;
}) {
  return (
    <div
      className={`rounded-md px-3 py-2 text-sm font-medium ${
        available
          ? "bg-emerald-50 text-emerald-800"
          : "bg-slate-100 text-slate-600"
      }`}
    >
      {label}: {available ? "Available" : "Not returned"}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-slate-50 p-3">
      <dt className="text-xs font-medium uppercase text-slate-500">{label}</dt>
      <dd className="mt-1 break-words text-sm font-semibold text-slate-950">
        {value}
      </dd>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex min-h-32 items-center justify-center bg-slate-50 px-4 py-8 text-center text-sm leading-6 text-slate-500">
      {text}
    </div>
  );
}
