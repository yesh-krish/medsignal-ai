"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { Drug, MedicationList } from "@/lib/api-types";

export default function MedicationCabinetPage() {
  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
  const [medicationList, setMedicationList] = useState<MedicationList | null>(null);
  const [query, setQuery] = useState("");
  const [searchResult, setSearchResult] = useState<Drug | null>(null);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMedicationList() {
      setIsLoadingList(true);
      setError(null);
      try {
        const response = await fetch(`${backendUrl}/api/medication-lists/default`);
        if (!response.ok) {
          throw new Error("Medication cabinet could not be loaded.");
        }
        setMedicationList((await response.json()) as MedicationList);
      } catch (caughtError) {
        setError(
          caughtError instanceof Error
            ? caughtError.message
            : "Medication cabinet could not be loaded.",
        );
      } finally {
        setIsLoadingList(false);
      }
    }

    void loadMedicationList();
  }, [backendUrl]);

  async function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedQuery = query.trim();
    if (!cleanedQuery) {
      setError("Enter a medication name.");
      return;
    }

    setIsSearching(true);
    setSearchResult(null);
    setError(null);
    try {
      const response = await fetch(
        `${backendUrl}/api/drugs/search?query=${encodeURIComponent(cleanedQuery)}`,
      );
      if (response.status === 404) {
        throw new Error("No matching medication found.");
      }
      if (!response.ok) {
        throw new Error("Medication search is unavailable right now.");
      }
      setSearchResult((await response.json()) as Drug);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Medication search failed.",
      );
    } finally {
      setIsSearching(false);
    }
  }

  async function handleAddDrug(drug: Drug) {
    setIsSaving(true);
    setError(null);
    try {
      const response = await fetch(
        `${backendUrl}/api/medication-lists/default/items`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ drug_id: drug.id }),
        },
      );
      if (!response.ok) {
        throw new Error("Medication could not be added.");
      }
      setMedicationList((await response.json()) as MedicationList);
      setSearchResult(null);
      setQuery("");
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Medication could not be added.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleRemoveItem(itemId: number) {
    setIsSaving(true);
    setError(null);
    try {
      const response = await fetch(
        `${backendUrl}/api/medication-lists/default/items/${itemId}`,
        { method: "DELETE" },
      );
      if (!response.ok) {
        throw new Error("Medication could not be removed.");
      }
      setMedicationList((await response.json()) as MedicationList);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Medication could not be removed.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  const hasItems = (medicationList?.items.length ?? 0) > 0;

  return (
    <main className="min-h-screen bg-[#f7faf9] px-6 py-6 text-slate-950">
      <div className="mx-auto max-w-6xl">
        <header className="border-b border-slate-200 pb-6">
          <div className="flex flex-wrap items-center gap-4">
            <Link href="/medsignal-ai" className="text-sm font-medium text-teal-700">
              Back to MedSignal AI
            </Link>
            <Link
              href="/medsignal-ai/compare"
              className="text-sm font-medium text-slate-600 transition hover:text-slate-950"
            >
              Compare medications
            </Link>
          </div>
          <p className="mt-5 text-sm font-medium uppercase text-teal-700">
            Medication cabinet
          </p>
          <h1 className="mt-2 text-4xl font-semibold tracking-normal">
            Build your medication list
          </h1>
          <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-600">
            Add RxNorm-normalized medications to prepare for potential
            drug-drug interaction screening. This is an educational preparation
            tool and does not replace a clinician or pharmacist review.
          </p>
        </header>

        <section className="mt-6 grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
          <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-950">
              Add a medication
            </h2>
            <form onSubmit={handleSearch} className="mt-4">
              <label
                htmlFor="cabinet-medication-search"
                className="mb-3 block text-sm font-medium text-slate-700"
              >
                Medication name
              </label>
              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  id="cabinet-medication-search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search medications"
                  className="h-12 min-w-0 flex-1 rounded-md border border-slate-300 bg-white px-4 text-base outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
                />
                <button
                  type="submit"
                  disabled={isSearching || isSaving}
                  className="h-12 rounded-md bg-teal-700 px-5 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {isSearching ? "Searching" : "Search"}
                </button>
              </div>
            </form>

            {searchResult && (
              <div className="mt-5 rounded-md border border-teal-200 bg-teal-50 p-4">
                <p className="text-sm font-semibold text-slate-950">
                  {searchResult.normalized_name ?? searchResult.input_name}
                </p>
                <p className="mt-1 text-xs leading-5 text-slate-600">
                  RxCUI {searchResult.rxcui ?? "unknown"} · TTY{" "}
                  {searchResult.tty ?? "unknown"}
                </p>
                <button
                  type="button"
                  onClick={() => handleAddDrug(searchResult)}
                  disabled={isSaving}
                  className="mt-4 h-10 rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {isSaving ? "Adding" : "Add to cabinet"}
                </button>
              </div>
            )}

            {error && (
              <p className="mt-4 rounded-md bg-rose-50 px-4 py-3 text-sm font-medium text-rose-800">
                {error}
              </p>
            )}
          </article>

          <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-950">
                  {medicationList?.name ?? "My medications"}
                </h2>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Review this list with your physician or pharmacist before
                  making medication decisions.
                </p>
              </div>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                {medicationList?.items.length ?? 0} medications
              </span>
            </div>

            {isLoadingList && (
              <div className="mt-5 space-y-3">
                {[0, 1, 2].map((item) => (
                  <div
                    key={item}
                    className="h-20 animate-pulse rounded-md bg-slate-100"
                  />
                ))}
              </div>
            )}

            {!isLoadingList && !hasItems && (
              <p className="mt-5 rounded-md bg-slate-50 px-4 py-4 text-sm leading-6 text-slate-500">
                No medications have been added yet. Search for a medication to
                start building the cabinet.
              </p>
            )}

            {!isLoadingList && hasItems && (
              <div className="mt-5 space-y-3">
                {medicationList?.items.map((item) => (
                  <div
                    key={item.id}
                    className="flex flex-col gap-4 rounded-md border border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <p className="font-semibold text-slate-950">
                        {item.drug.normalized_name ?? item.drug.input_name}
                      </p>
                      <p className="mt-1 text-xs leading-5 text-slate-500">
                        RxCUI {item.drug.rxcui ?? "unknown"} ·{" "}
                        {item.drug.synonym ?? "No synonym returned"}
                      </p>
                    </div>
                    <div className="flex gap-3">
                      <Link
                        href={`/medsignal-ai/drugs/${item.drug.id}`}
                        className="inline-flex h-10 items-center rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                      >
                        Dashboard
                      </Link>
                      <button
                        type="button"
                        onClick={() => handleRemoveItem(item.id)}
                        disabled={isSaving}
                        className="h-10 rounded-md bg-rose-50 px-3 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:text-slate-400"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </article>
        </section>

        <section className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-950 shadow-sm">
          This cabinet is for education and appointment preparation. It does not
          detect interactions yet, and it should not be used to start, stop, or
          change prescribed medication without medical advice.
        </section>
      </div>
    </main>
  );
}
