type LoadingCardProps = {
  title?: string;
  lines?: number;
  height?: "sm" | "md" | "lg";
};

const heightClasses = {
  sm: "min-h-36",
  md: "min-h-64",
  lg: "min-h-80",
};

export function LoadingCard({
  title = "Loading",
  lines = 4,
  height = "md",
}: LoadingCardProps) {
  return (
    <section
      className={`rounded-lg border border-slate-200 bg-white p-5 shadow-sm ${heightClasses[height]}`}
      aria-busy="true"
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase text-teal-700">
            Loading
          </p>
          <h2 className="mt-2 text-lg font-semibold text-slate-950">{title}</h2>
        </div>
        <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full w-2/3 animate-pulse rounded-full bg-teal-600" />
        </div>
      </div>
      <div className="mt-6 space-y-3">
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={`${title}-${index}`}
            className="h-3 animate-pulse rounded-full bg-slate-100"
            style={{ width: `${92 - index * 12}%` }}
          />
        ))}
      </div>
    </section>
  );
}
