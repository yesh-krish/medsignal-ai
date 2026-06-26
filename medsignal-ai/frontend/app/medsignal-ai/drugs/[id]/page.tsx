"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { DataProvenancePanel } from "@/components/DataProvenancePanel";
import { DisclaimerCard } from "@/components/DisclaimerCard";
import { DrugIdentityCard } from "@/components/DrugIdentityCard";
import { DrugSearchBar } from "@/components/DrugSearchBar";
import { LabelSectionCard } from "@/components/LabelSectionCard";
import { LoadingCard } from "@/components/LoadingCard";
import { ReactionBarChart } from "@/components/ReactionBarChart";
import { ReportsOverTimeChart } from "@/components/ReportsOverTimeChart";
import { SafetyAlertsCard } from "@/components/SafetyAlertsCard";
import { SignalAnalysisPanel } from "@/components/SignalAnalysisPanel";
import { SignalTimelinePanel } from "@/components/SignalTimelinePanel";
import { SeriousnessBreakdownChart } from "@/components/SeriousnessBreakdownChart";
import type {
  Drug,
  DrugLabel,
  EventTrends,
  IngestionRun,
  SafetyAlert,
  SafetySummary,
  SignalAnalysis,
  SignalAnalysisRun,
  SignalTimeline,
} from "@/lib/api-types";

type PageProps = {
  params: {
    id: string;
  };
};

const emptyTrends: EventTrends = {
  top_reported_reactions: [],
  reports_by_year: {},
  seriousness_breakdown: {},
  sex_breakdown: {},
  total_reports: 0,
};

export default function DrugDashboard({ params }: PageProps) {
  const [drug, setDrug] = useState<Drug | null>(null);
  const [label, setLabel] = useState<DrugLabel | null>(null);
  const [ingestionRun, setIngestionRun] = useState<IngestionRun | null>(null);
  const [alerts, setAlerts] = useState<SafetyAlert[]>([]);
  const [summary, setSummary] = useState<SafetySummary | null>(null);
  const [signalAnalysis, setSignalAnalysis] = useState<SignalAnalysis | null>(null);
  const [signalHistory, setSignalHistory] = useState<SignalAnalysisRun[]>([]);
  const [signalTimeline, setSignalTimeline] = useState<SignalTimeline | null>(null);
  const [trends, setTrends] = useState<EventTrends>(emptyTrends);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshingReports, setIsRefreshingReports] = useState(false);
  const [isRefreshingTrends, setIsRefreshingTrends] = useState(false);
  const [isLoadingTrends, setIsLoadingTrends] = useState(false);
  const [isLoadingLabel, setIsLoadingLabel] = useState(false);
  const [isLoadingSignals, setIsLoadingSignals] = useState(false);
  const [isLoadingAlerts, setIsLoadingAlerts] = useState(false);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [isAnalyzingSignals, setIsAnalyzingSignals] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trendsError, setTrendsError] = useState<string | null>(null);
  const [alertsError, setAlertsError] = useState<string | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [signalError, setSignalError] = useState<string | null>(null);
  const loadedDashboardKey = useRef<string | null>(null);

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

  useEffect(() => {
    async function loadDashboard() {
      const dashboardKey = `${backendUrl}:${params.id}`;
      if (loadedDashboardKey.current === dashboardKey) return;
      loadedDashboardKey.current = dashboardKey;

      setIsLoading(true);
      setIsRefreshingReports(true);
      setIsRefreshingTrends(false);
      setIsLoadingTrends(false);
      setIsLoadingLabel(false);
      setIsLoadingSignals(false);
      setIsLoadingAlerts(false);
      setDrug(null);
      setLabel(null);
      setIngestionRun(null);
      setAlerts([]);
      setSummary(null);
      setSignalAnalysis(null);
      setSignalHistory([]);
      setSignalTimeline(null);
      setTrends(emptyTrends);
      setError(null);
      setTrendsError(null);
      setAlertsError(null);
      setSummaryError(null);
      setSignalError(null);

      try {
        const drugResponse = await fetch(`${backendUrl}/api/drugs/${params.id}`);
        if (!drugResponse.ok) {
          throw new Error("Drug identity could not be loaded.");
        }
        const drugData = (await drugResponse.json()) as Drug;
        setDrug(drugData);
        setIsLoading(false);
        setIsLoadingTrends(true);
        setIsLoadingLabel(true);
        setIsLoadingSignals(true);
        setIsLoadingAlerts(true);

        const labelPromise = fetch(`${backendUrl}/api/drugs/${params.id}/label`);
        const eventsPromise = fetch(
          `${backendUrl}/api/drugs/${params.id}/events?limit=100`,
        );
        const trendsPromise = fetch(
          `${backendUrl}/api/drugs/${params.id}/event-trends`,
        );
        const alertsPromise = fetch(
          `${backendUrl}/api/drugs/${params.id}/alerts`,
        );
        const signalsPromise = fetch(
          `${backendUrl}/api/drugs/${params.id}/signals/latest`,
        );
        const signalHistoryPromise = fetch(
          `${backendUrl}/api/drugs/${params.id}/signals/history`,
        );
        const signalTimelinePromise = fetch(
          `${backendUrl}/api/drugs/${params.id}/signals/timeline`,
        );

        eventsPromise
          .then((eventsResponse) => {
            if (!eventsResponse.ok) {
              throw new Error("Reported adverse events could not be loaded.");
            }
            return fetch(
              `${backendUrl}/api/drugs/${params.id}/ingestion-runs/latest`,
            );
          })
          .then(async (ingestionResponse) => {
            if (ingestionResponse.ok) {
              setIngestionRun(
                (await ingestionResponse.json()) as IngestionRun | null,
              );
            }
          })
          .catch(() => {
            setTrendsError("Reported adverse event refresh could not be loaded.");
          })
          .finally(() => setIsRefreshingReports(false));

        trendsPromise
          .then(async (trendsResponse) => {
            if (!trendsResponse.ok) {
              throw new Error("Reported adverse event trends could not be loaded.");
            }
            setTrends((await trendsResponse.json()) as EventTrends);
          })
          .catch((caughtError) => {
            setTrendsError(
              caughtError instanceof Error
                ? caughtError.message
                : "Reported adverse event trends could not be loaded.",
            );
          })
          .finally(() => setIsLoadingTrends(false));

        alertsPromise
          .then(async (alertsResponse) => {
            if (!alertsResponse.ok) {
              throw new Error("Potential safety signals could not be loaded.");
            }
            setAlerts((await alertsResponse.json()) as SafetyAlert[]);
          })
          .catch(() => {
            setAlertsError("Potential safety signals could not be loaded.");
          })
          .finally(() => setIsLoadingAlerts(false));

        Promise.all([
          signalsPromise,
          signalHistoryPromise,
          signalTimelinePromise,
        ])
          .then(
            async ([
              signalsResponse,
              signalHistoryResponse,
              signalTimelineResponse,
            ]) => {
              if (signalsResponse.ok) {
                setSignalAnalysis(
                  (await signalsResponse.json()) as SignalAnalysis | null,
                );
              }
              if (signalHistoryResponse.ok) {
                setSignalHistory(
                  (await signalHistoryResponse.json()) as SignalAnalysisRun[],
                );
              }
              if (signalTimelineResponse.ok) {
                setSignalTimeline(
                  (await signalTimelineResponse.json()) as SignalTimeline,
                );
              }
            },
          )
          .catch(() => {
            setSignalError("PRR/ROR signal history could not be loaded.");
          })
          .finally(() => setIsLoadingSignals(false));

        labelPromise
          .then(async (labelResponse) => {
            if (labelResponse.status === 504) {
              throw new Error("openFDA label request timed out.");
            }
            if (!labelResponse.ok) {
              throw new Error("FDA label could not be loaded.");
            }
            setLabel((await labelResponse.json()) as DrugLabel | null);
          })
          .catch((caughtError) => {
            setSummaryError(
              caughtError instanceof Error
                ? caughtError.message
                : "FDA label could not be loaded.",
            );
          })
          .finally(() => setIsLoadingLabel(false));
      } catch (caughtError) {
        loadedDashboardKey.current = null;
        setError(
          caughtError instanceof Error
            ? caughtError.message
            : "Drug dashboard could not be loaded.",
        );
      } finally {
        setIsRefreshingReports(false);
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, [backendUrl, params.id]);

  async function handleGenerateSummary() {
    setIsGeneratingSummary(true);
    setSummaryError(null);
    setSummary(null);

    try {
      const response = await fetch(
        `${backendUrl}/api/drugs/${params.id}/summarize-label`,
        { method: "POST" },
      );
      if (response.status === 502) {
        throw new Error("The AI summarizer is unavailable right now.");
      }
      if (!response.ok) {
        throw new Error("AI safety summary could not be generated.");
      }
      const data = (await response.json()) as SafetySummary;
      setSummary(data);
    } catch (caughtError) {
      setSummaryError(
        caughtError instanceof Error
          ? caughtError.message
          : "AI safety summary could not be generated.",
      );
    } finally {
      setIsGeneratingSummary(false);
    }
  }

  async function handleAnalyzeSignals() {
    setIsAnalyzingSignals(true);
    setSignalError(null);
    try {
      const response = await fetch(
        `${backendUrl}/api/drugs/${params.id}/signals/analyze`,
        { method: "POST" },
      );
      if (response.status === 504) {
        throw new Error("openFDA signal analysis timed out. Try again shortly.");
      }
      if (!response.ok) {
        throw new Error("PRR/ROR signal analysis could not be completed.");
      }
      const analysis = (await response.json()) as SignalAnalysis;
      setSignalAnalysis(analysis);
      setSignalHistory((current) => [
        analysis.run,
        ...current.filter((run) => run.id !== analysis.run.id),
      ]);
      const timelineResponse = await fetch(
        `${backendUrl}/api/drugs/${params.id}/signals/timeline`,
      );
      if (timelineResponse.ok) {
        setSignalTimeline((await timelineResponse.json()) as SignalTimeline);
      }
    } catch (caughtError) {
      setSignalError(
        caughtError instanceof Error
          ? caughtError.message
          : "PRR/ROR signal analysis failed.",
      );
    } finally {
      setIsAnalyzingSignals(false);
    }
  }

  async function handleRefreshTrends() {
    setIsRefreshingTrends(true);
      setTrendsError(null);
      setIsLoadingTrends(true);
      try {
      const response = await fetch(
        `${backendUrl}/api/drugs/${params.id}/event-trends?refresh=true`,
      );
      if (response.status === 504) {
        throw new Error("openFDA trend refresh timed out. Try again shortly.");
      }
      if (!response.ok) {
        throw new Error("Reported adverse event trends could not be refreshed.");
      }
      setTrends((await response.json()) as EventTrends);
    } catch (caughtError) {
      setTrendsError(
        caughtError instanceof Error
          ? caughtError.message
          : "Reported adverse event trends could not be refreshed.",
      );
      } finally {
      setIsLoadingTrends(false);
      setIsRefreshingTrends(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f7faf9] px-6 py-6">
      <div className="mx-auto max-w-7xl">
        <header className="flex flex-col gap-5 border-b border-slate-200 pb-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Link
              href="/medsignal-ai"
              className="text-sm font-medium text-teal-700"
            >
              Back to search
            </Link>
            <Link
              href="/medsignal-ai/compare"
              className="ml-4 text-sm font-medium text-slate-600 transition hover:text-slate-950"
            >
              Compare medications
            </Link>
            <p className="mt-5 text-sm font-medium uppercase text-teal-700">
              Medication safety dashboard
            </p>
            <h1 className="mt-2 text-4xl font-semibold tracking-normal text-slate-950">
              {drug?.normalized_name ?? "Medication"}
            </h1>
          </div>
          <div className="w-full max-w-xl rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <DrugSearchBar compact />
          </div>
        </header>

        {isLoading && (
          <div className="mt-6 rounded-lg border border-slate-200 bg-white p-5 text-slate-700 shadow-sm">
            Loading dashboard data...
          </div>
        )}

        {error && (
          <div className="mt-6 rounded-lg border border-rose-200 bg-rose-50 p-5 font-medium text-rose-800 shadow-sm">
            {error}
          </div>
        )}

        {!isLoading && !error && drug && (
          <div className="mt-6 space-y-6">
            <DrugIdentityCard drug={drug} totalReports={trends.total_reports} />

            {isRefreshingReports ? (
              <LoadingCard
                title="Data provenance"
                lines={4}
                height="sm"
              />
            ) : (
              <DataProvenancePanel run={ingestionRun} />
            )}

            {isLoadingSignals ? (
              <LoadingCard
                title="PRR/ROR signal analysis"
                lines={5}
                height="lg"
              />
            ) : (
              <SignalAnalysisPanel
                analysis={signalAnalysis}
                history={signalHistory}
                isAnalyzing={isAnalyzingSignals}
                error={signalError}
                onAnalyze={handleAnalyzeSignals}
              />
            )}

            {isLoadingSignals ? (
              <LoadingCard
                title="Historical signal tracking"
                lines={5}
                height="md"
              />
            ) : (
              <SignalTimelinePanel timeline={signalTimeline} />
            )}

            {trendsError && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm font-medium text-amber-900">
                {trendsError}
              </div>
            )}

            {trends.total_reports === 0 && (
              <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-950">
                      Reported adverse event trends
                    </h2>
                    <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-600">
                      No cached trend data is available for this medication yet.
                      Refreshing pulls aggregate counts from openFDA and may take
                      a little while the first time.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleRefreshTrends}
                    disabled={isRefreshingTrends}
                    className="h-11 rounded-md bg-teal-700 px-4 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                  >
                    {isRefreshingTrends ? "Refreshing trends" : "Refresh trends"}
                  </button>
                </div>
              </div>
            )}

            <section className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
              {isLoadingTrends ? (
                <LoadingCard title="Top reported reactions" height="lg" />
              ) : (
                <ReactionBarChart data={trends.top_reported_reactions} />
              )}
              {isLoadingTrends ? (
                <LoadingCard title="Serious vs non-serious" height="lg" />
              ) : (
                <SeriousnessBreakdownChart
                  seriousnessBreakdown={trends.seriousness_breakdown}
                />
              )}
            </section>

            <section className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
              {isLoadingTrends ? (
                <LoadingCard title="Reports by year" height="md" />
              ) : (
                <ReportsOverTimeChart reportsByYear={trends.reports_by_year} />
              )}
              {isLoadingAlerts ? (
                <LoadingCard title="Recent reporting increases" height="md" />
              ) : (
                <SafetyAlertsCard alerts={alerts} error={alertsError} />
              )}
            </section>

            <DisclaimerCard />

            {isLoadingLabel ? (
              <LoadingCard title="AI safety summary" height="sm" />
            ) : (
              <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">
                    AI safety summary
                  </h2>
                  <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">
                    Generate a plain-English summary from FDA label warnings,
                    boxed warnings, adverse reactions, and contraindications.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleGenerateSummary}
                  disabled={isGeneratingSummary || !label}
                  className="h-11 rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {isGeneratingSummary
                    ? "Generating summary"
                    : "Generate AI Safety Summary"}
                </button>
              </div>
              {!label && (
                <p className="mt-4 rounded-md bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-500">
                  No FDA label sections are available yet, so the AI safety
                  summary cannot be generated for this medication.
                </p>
              )}
              {summaryError && (
                <p className="mt-4 rounded-md bg-rose-50 px-4 py-3 text-sm font-medium text-rose-800">
                  {summaryError}
                </p>
              )}
              {summary && (
                <div className="mt-5 rounded-md bg-slate-50 p-4">
                  <p className="text-sm leading-6 text-slate-800">
                    {summary.summary_text}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-3 text-xs font-medium text-slate-500">
                    <span>Model: {summary.model_name}</span>
                    <span>Latency: {summary.latency_ms} ms</span>
                    <span>Output: {summary.output_length} chars</span>
                  </div>
                  <p className="mt-4 border-t border-slate-200 pt-4 text-xs leading-5 text-slate-500">
                    {summary.disclaimer}
                  </p>
                </div>
              )}
              </section>
            )}

            <section className="grid gap-5 lg:grid-cols-2">
              {isLoadingLabel ? (
                <>
                  <LoadingCard title="FDA label warnings" height="md" />
                  <LoadingCard title="FDA adverse reactions" height="md" />
                  <LoadingCard title="FDA contraindications" height="md" />
                  <LoadingCard title="FDA boxed warning" height="md" />
                </>
              ) : (
                <>
                  <LabelSectionCard
                    title="FDA label warnings"
                    items={label?.warnings ?? null}
                    accent="rose"
                  />
                  <LabelSectionCard
                    title="FDA adverse reactions"
                    items={label?.adverse_reactions ?? null}
                    accent="teal"
                  />
                  <LabelSectionCard
                    title="FDA contraindications"
                    items={label?.contraindications ?? null}
                    accent="blue"
                  />
                  <LabelSectionCard
                    title="FDA boxed warning"
                    items={label?.boxed_warning ?? null}
                    accent="slate"
                  />
                </>
              )}
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
