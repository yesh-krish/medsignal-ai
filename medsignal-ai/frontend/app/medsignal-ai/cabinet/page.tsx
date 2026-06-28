"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { Drug, InteractionScreening, MedicationList } from "@/lib/api-types";

export default function MedicationCabinetPage() {
  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
  const [medicationList, setMedicationList] = useState<MedicationList | null>(null);
  const [query, setQuery] = useState("");
  const [searchResult, setSearchResult] = useState<Drug | null>(null);
  const [interactionScreening, setInteractionScreening] =
    useState<InteractionScreening | null>(null);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isScreeningInteractions, setIsScreeningInteractions] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [interactionError, setInteractionError] = useState<string | null>(null);

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
      setInteractionScreening(null);
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
      setInteractionScreening(null);
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

  async function handleScreenInteractions() {
    setIsScreeningInteractions(true);
    setInteractionError(null);
    try {
      const response = await fetch(
        `${backendUrl}/api/medication-lists/default/interactions`,
      );
      if (response.status === 504) {
        throw new Error(
          "openFDA label interaction screening timed out. Try again shortly.",
        );
      }
      if (!response.ok) {
        throw new Error("Potential interaction screening could not be completed.");
      }
      setInteractionScreening((await response.json()) as InteractionScreening);
    } catch (caughtError) {
      setInteractionError(
        caughtError instanceof Error
          ? caughtError.message
          : "Potential interaction screening failed.",
      );
    } finally {
      setIsScreeningInteractions(false);
    }
  }

  const hasItems = (medicationList?.items.length ?? 0) > 0;
  const formatAssessmentValue = (value: string | null) =>
    value ? value.replaceAll("_", " ") : "Not classified";

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
            drug-drug interaction screening from FDA label text. This is an
            educational preparation tool and does not replace a clinician or
            pharmacist review.
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
                  RxCUI {searchResult.rxcui ?? "unknown"} / TTY{" "}
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
                        RxCUI {item.drug.rxcui ?? "unknown"} /{" "}
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

        <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-sm font-medium uppercase text-teal-700">
                Interaction screening
              </p>
              <h2 className="mt-2 text-xl font-semibold text-slate-950">
                Potential drug-drug interactions
              </h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                Screen the current cabinet against openFDA label
                drug_interactions text. Matched cards include FDA label evidence
                to discuss with a clinician or pharmacist.
              </p>
            </div>
            <button
              type="button"
              onClick={handleScreenInteractions}
              disabled={
                isScreeningInteractions ||
                isSaving ||
                (medicationList?.items.length ?? 0) < 2
              }
              className="h-11 shrink-0 rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isScreeningInteractions
                ? "Screening"
                : "Screen potential interactions"}
            </button>
          </div>

          {(medicationList?.items.length ?? 0) < 2 && (
            <p className="mt-4 rounded-md bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-500">
              Add at least two medications to screen for potential interactions.
            </p>
          )}

          {interactionError && (
            <p className="mt-4 rounded-md bg-rose-50 px-4 py-3 text-sm font-medium text-rose-800">
              {interactionError}
            </p>
          )}

          {interactionScreening && (
            <div className="mt-5">
              {interactionScreening.interactions.length === 0 ? (
                <p className="rounded-md bg-emerald-50 px-4 py-3 text-sm leading-6 text-emerald-800">
                  openFDA labels did not return drug_interactions text for the
                  checked medications. This does not rule out a clinically
                  important interaction.
                </p>
              ) : (
                <div className="space-y-3">
                  {interactionScreening.interactions.map((interaction, index) => (
                    <article
                      key={`${interaction.description}-${index}`}
                      className="rounded-md border border-amber-200 bg-amber-50 p-4"
                    >
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <h3 className="text-sm font-semibold text-amber-950">
                          {interaction.drugs.map((drug) => drug.name).join(" + ")}
                        </h3>
                        <span className="w-fit rounded-full bg-white px-3 py-1 text-xs font-semibold text-amber-800">
                          {interaction.severity ?? "Severity not specified"}
                        </span>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-amber-950">
                        {interaction.description}
                      </p>
                      <div className="mt-3 grid gap-2 sm:grid-cols-3">
                        <div className="rounded-md bg-white px-3 py-2">
                          <p className="text-xs font-semibold uppercase text-amber-800">
                            Mechanism
                          </p>
                          <p className="mt-1 text-sm font-semibold capitalize text-slate-950">
                            {formatAssessmentValue(interaction.mechanism)}
                          </p>
                        </div>
                        <div className="rounded-md bg-white px-3 py-2">
                          <p className="text-xs font-semibold uppercase text-amber-800">
                            Risk category
                          </p>
                          <p className="mt-1 text-sm font-semibold capitalize text-slate-950">
                            {formatAssessmentValue(interaction.risk_category)}
                          </p>
                        </div>
                        <div className="rounded-md bg-white px-3 py-2">
                          <p className="text-xs font-semibold uppercase text-amber-800">
                            Severity tier
                          </p>
                          <p className="mt-1 text-sm font-semibold capitalize text-slate-950">
                            {formatAssessmentValue(interaction.severity_tier)}
                          </p>
                        </div>
                      </div>
                      {interaction.explanation && (
                        <p className="mt-2 text-sm leading-6 text-amber-900">
                          {interaction.explanation}
                        </p>
                      )}
                      {interaction.assessment_reason && (
                        <p className="mt-2 rounded-md bg-white px-3 py-2 text-sm leading-6 text-slate-700">
                          {interaction.assessment_reason}
                        </p>
                      )}
                      {((interaction.detected_classes?.length ?? 0) > 0 ||
                        (interaction.reasoning_steps?.length ?? 0) > 0) && (
                        <div className="mt-3 rounded-md border border-slate-200 bg-white p-3">
                          <p className="text-xs font-semibold uppercase text-slate-600">
                            Why this was flagged
                          </p>
                          {interaction.detected_classes &&
                            interaction.detected_classes.length > 0 && (
                              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                                {interaction.detected_classes.map((detectedClass) => (
                                  <div
                                    key={`${detectedClass.rxcui}-${detectedClass.drug_name}`}
                                    className="rounded-md bg-slate-50 px-3 py-2"
                                  >
                                    <p className="text-sm font-semibold text-slate-950">
                                      {detectedClass.drug_name}
                                    </p>
                                    <p className="mt-1 text-xs leading-5 text-slate-500">
                                      {detectedClass.classes.length > 0
                                        ? detectedClass.classes
                                            .map(formatAssessmentValue)
                                            .join(", ")
                                        : "No class category detected"}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            )}
                          {interaction.reasoning_steps &&
                            interaction.reasoning_steps.length > 0 && (
                              <ol className="mt-3 space-y-2">
                                {interaction.reasoning_steps.map((step, stepIndex) => (
                                  <li
                                    key={`${step}-${stepIndex}`}
                                    className="flex gap-3 text-sm leading-6 text-slate-700"
                                  >
                                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-950 text-xs font-semibold text-white">
                                      {stepIndex + 1}
                                    </span>
                                    <span>{step}</span>
                                  </li>
                                ))}
                              </ol>
                            )}
                        </div>
                      )}
                      {interaction.evidence && interaction.evidence.length > 0 && (
                        <div className="mt-3 rounded-md border border-amber-200 bg-white p-3">
                          <p className="text-xs font-semibold uppercase text-amber-800">
                            FDA label evidence
                          </p>
                          <div className="mt-2 space-y-2">
                            {interaction.evidence.map((evidence, excerptIndex) => (
                              <div
                                key={`${evidence.source_rxcui}-${evidence.excerpt}-${excerptIndex}`}
                                className="rounded-md bg-slate-50 p-3"
                              >
                                <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                                  <p className="text-sm font-semibold text-slate-950">
                                    From {evidence.source_drug_name} label
                                  </p>
                                  <span className="w-fit rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-slate-600">
                                    {evidence.match_type}
                                  </span>
                                </div>
                                {evidence.matched_drug_name && evidence.matched_term && (
                                  <p className="mt-2 text-xs leading-5 text-slate-500">
                                    Matched to {evidence.matched_drug_name} using{" "}
                                    <span className="font-semibold text-slate-700">
                                      {evidence.matched_term}
                                    </span>{" "}
                                    in {evidence.label_section}.
                                  </p>
                                )}
                                {evidence.risk_statement && (
                                  <div className="mt-3 rounded-md border border-rose-200 bg-rose-50 px-3 py-2">
                                    <p className="text-xs font-semibold uppercase text-rose-800">
                                      Potential concern described in FDA label
                                    </p>
                                    <p className="mt-1 text-sm leading-6 text-rose-950">
                                      {evidence.risk_statement}
                                    </p>
                                  </div>
                                )}
                                <p className="mt-2 text-sm leading-6 text-slate-700">
                                  {evidence.excerpt}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      <p className="mt-3 text-xs font-medium uppercase text-amber-800">
                        Source: {interaction.source}
                      </p>
                    </article>
                  ))}
                </div>
              )}
              <p className="mt-4 border-t border-slate-200 pt-4 text-xs leading-5 text-slate-500">
                {interactionScreening.disclaimer}
              </p>
            </div>
          )}
        </section>

        <section className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-950 shadow-sm">
          This cabinet is for education and appointment preparation. It does not
          replace professional medication review, and it should not be used to
          start, stop, or change prescribed medication without medical advice.
        </section>
      </div>
    </main>
  );
}
