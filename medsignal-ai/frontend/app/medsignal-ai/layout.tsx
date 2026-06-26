import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MedSignal AI | Medication Safety Intelligence",
  description:
    "Explore FDA label information, reported adverse events, and potential safety signals.",
};

export default function MedSignalLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return children;
}
