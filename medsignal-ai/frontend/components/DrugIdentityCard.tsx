import type { Drug } from "@/lib/api-types";

type DrugIdentityCardProps = {
  drug: Drug;
  totalReports: number;
};

export function DrugIdentityCard({ drug, totalReports }: DrugIdentityCardProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-medium uppercase text-teal-700">
            Drug identity
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-normal text-slate-950">
            {drug.normalized_name ?? drug.input_name}
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Dashboard view of FDA label sections and reported adverse events
            from reports mentioning this medication.
          </p>
        </div>
        <div className="rounded-md bg-slate-950 px-4 py-3 text-white">
          <p className="text-xs font-medium uppercase text-slate-300">
            Total reports
          </p>
          <p className="mt-1 text-2xl font-semibold">{totalReports}</p>
        </div>
      </div>

      <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <IdentityItem label="RxCUI" value={drug.rxcui} />
        <IdentityItem label="Input name" value={drug.input_name} />
        <IdentityItem label="Synonym" value={drug.synonym} />
        <IdentityItem label="TTY" value={drug.tty} />
      </dl>
    </section>
  );
}

function IdentityItem({
  label,
  value,
}: {
  label: string;
  value?: string | null;
}) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase text-slate-500">{label}</dt>
      <dd className="mt-1 break-words text-sm font-semibold text-slate-950">
        {value || "Unavailable"}
      </dd>
    </div>
  );
}
