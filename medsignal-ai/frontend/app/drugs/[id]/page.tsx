import { redirect } from "next/navigation";

type PageProps = {
  params: {
    id: string;
  };
};

export default function LegacyDrugDashboard({ params }: PageProps) {
  redirect(`/medsignal-ai/drugs/${params.id}`);
}
