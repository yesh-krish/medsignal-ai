"use client";

import { useEffect, useState } from "react";

type HealthState = "checking" | "ok" | "error";

export default function Home() {
  const [query, setQuery] = useState("");
  const [health, setHealth] = useState<HealthState>("checking");

  useEffect(() => {
    const backendUrl =
      process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

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
  }, []);

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
            A clean local scaffold for searching medication names and building
            clinical signal workflows over time.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <label
              htmlFor="medication-search"
              className="mb-3 block text-sm font-medium text-slate-700"
            >
              Medication name
            </label>
            <input
              id="medication-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search medications"
              className="h-12 w-full rounded-md border border-slate-300 bg-white px-4 text-base text-slate-950 outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
            />
            <div className="mt-4 min-h-12 rounded-md bg-slate-50 px-4 py-3 text-sm text-slate-600">
              {query
                ? `Ready to search for "${query}" once medication search is wired.`
                : "Enter a medication name to begin."}
            </div>
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
