"use client";

import { useEffect, useState } from "react";

import { DrugSearchBar } from "@/components/DrugSearchBar";

type HealthState = "checking" | "ok" | "error";

export default function Home() {
  const [health, setHealth] = useState<HealthState>("checking");

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

  useEffect(() => {
    fetch(`${backendUrl}/health`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Health check failed");
        }
        return response.json();
      })
      .then((data: { status?: string }) => {
        setHealth(data.status === "ok" ? "ok" : "error");
      })
      .catch(() => setHealth("error"));
  }, [backendUrl]);

  return (
    <main className="min-h-screen bg-[#f7faf9]">
      <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col justify-center px-6 py-12">
        <div className="mb-10">
          <p className="mb-3 text-sm font-medium uppercase text-teal-700">
            Medication intelligence
          </p>
          <h1 className="text-5xl font-semibold tracking-normal text-slate-950 sm:text-6xl">
            MedSignal AI
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
            Search a medication to open a safety dashboard with FDA label
            sections and reported adverse events.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <DrugSearchBar />
          </div>

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
      </section>
    </main>
  );
}
