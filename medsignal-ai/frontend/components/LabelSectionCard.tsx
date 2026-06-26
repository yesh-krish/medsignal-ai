type LabelSectionCardProps = {
  title: string;
  items: string[] | null;
  accent?: "rose" | "teal" | "blue" | "slate";
};

const accentClasses = {
  rose: "border-l-rose-600",
  teal: "border-l-teal-700",
  blue: "border-l-blue-700",
  slate: "border-l-slate-700",
};

export function LabelSectionCard({
  title,
  items,
  accent = "slate",
}: LabelSectionCardProps) {
  return (
    <article
      className={`rounded-lg border border-l-4 border-slate-200 bg-white p-5 shadow-sm ${accentClasses[accent]}`}
    >
      <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
      {items && items.length > 0 ? (
        <div className="mt-4 max-h-80 space-y-3 overflow-auto pr-2">
          {items.map((item, index) => (
            <p key={`${title}-${index}`} className="text-sm leading-6 text-slate-700">
              {item}
            </p>
          ))}
        </div>
      ) : (
        <p className="mt-4 rounded-md bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-500">
          This FDA label section was not returned for the selected medication.
        </p>
      )}
    </article>
  );
}
