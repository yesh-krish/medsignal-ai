"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { Drug } from "@/lib/api-types";

type DrugSearchBarProps = {
  compact?: boolean;
};

export function DrugSearchBar({ compact = false }: DrugSearchBarProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const cleanedQuery = query.trim();
    if (!cleanedQuery) {
      setError("Enter a medication name.");
      return;
    }

    setError(null);
    setIsSearching(true);

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
      router.push(`/drugs/${drug.id}`);
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

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <label
        htmlFor={compact ? "dashboard-medication-search" : "medication-search"}
        className="mb-3 block text-sm font-medium text-slate-700"
      >
        Medication name
      </label>
      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          id={compact ? "dashboard-medication-search" : "medication-search"}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search medications"
          className="h-12 min-w-0 flex-1 rounded-md border border-slate-300 bg-white px-4 text-base text-slate-950 outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
        />
        <button
          type="submit"
          disabled={isSearching}
          className="h-12 rounded-md bg-teal-700 px-5 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {isSearching ? "Searching" : "Search"}
        </button>
      </div>
      <div className={compact ? "mt-2 min-h-6" : "mt-4 min-h-6"}>
        {isSearching && (
          <p className="text-sm font-medium text-teal-800">Searching RxNorm...</p>
        )}
        {error && <p className="text-sm font-medium text-rose-700">{error}</p>}
      </div>
    </form>
  );
}
