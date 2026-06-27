"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { DrugSearchBar } from "@/components/DrugSearchBar";

type HealthState = "checking" | "ok" | "error";

export default function MedSignalHome() {
  const [health, setHealth] = useState<HealthState>("checking");
  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

  useEffect(() => {
    fetch(`${backendUrl}/health`)
      .then((response) => {
        if (!response.ok) throw new Error("Health check failed");
        return response.json();
      })
      .then((data: { status?: string }) => {
        setHealth(data.status === "ok" ? "ok" : "error");
      })
      .catch(() => setHealth("error"));
  }, [backendUrl]);

  return (
    <main className="min-h-screen bg-[#f7faf9] text-slate-950">
      <nav className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4">
          <Link href="/medsignal-ai" className="font-semibold text-slate-950">
            MedSignal AI
          </Link>
          <Link
            href="/"
            className="text-sm font-medium text-teal-700 transition hover:text-teal-900"
          >
            View portfolio
          </Link>
        </div>
      </nav>

      <section className="mx-auto flex min-h-[calc(100vh-65px)] w-full max-w-5xl flex-col justify-center px-6 py-12">
        <div className="mb-10">
          <p className="mb-3 text-sm font-medium uppercase text-teal-700">
            Medication safety intelligence
          </p>
          <h1 className="text-5xl font-semibold tracking-normal text-slate-950 sm:text-6xl">
            MedSignal AI
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
            Search a medication to explore normalized drug identity, FDA label
            sections, reported adverse event trends, data provenance, and
            potential safety signals.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
          <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <DrugSearchBar />
          </section>

          <aside className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-700">Backend health</p>
            <div className="mt-4 flex items-center gap-3">
              <span
                className={`h-3 w-3 rounded-full ${
                  health === "ok"
                    ? "bg-emerald-500"
                    : health === "checking"
                      ? "bg-amber-400"
                      : "bg-rose-500"
                }`}
              />
              <span className="text-base font-semibold capitalize text-slate-950">
                {health}
              </span>
            </div>
          </aside>
        </div>

        <div className="mt-5 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-950">
                Compare two medications
              </h2>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                Review reported adverse event patterns and FDA label section
                differences side by side.
              </p>
            </div>
            <Link
              href="/medsignal-ai/compare"
              className="inline-flex h-11 items-center justify-center rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              Open comparison
            </Link>
          </div>
        </div>

        <div className="mt-5 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-950">
                Build a medication cabinet
              </h2>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                Add multiple RxNorm-normalized medications before screening for
                potential drug-drug interactions in the next phase.
              </p>
            </div>
            <Link
              href="/medsignal-ai/cabinet"
              className="inline-flex h-11 items-center justify-center rounded-md bg-teal-700 px-4 text-sm font-semibold text-white transition hover:bg-teal-800"
            >
              Open cabinet
            </Link>
          </div>
        </div>

        <p className="mt-8 max-w-3xl text-sm leading-6 text-slate-500">
          Educational use only. Reported adverse events do not establish that a
          medication caused an event and are not medical advice.
        </p>
      </section>
    </main>
  );
}
