export function DisclaimerCard() {
  return (
    <section className="rounded-lg border border-amber-200 bg-amber-50 p-5 text-amber-950 shadow-sm">
      <h2 className="text-lg font-semibold">Educational use only</h2>
      <p className="mt-2 text-sm leading-6">
        This dashboard summarizes FDA label information and reported adverse
        events for exploration. It is not medical advice, diagnosis, or
        treatment guidance. Always talk with a qualified clinician or pharmacist
        about medication decisions.
      </p>
    </section>
  );
}
