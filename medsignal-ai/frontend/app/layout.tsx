import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Yeshas Krishna | Portfolio",
  description: "Interactive personal portfolio for Yeshas Krishna",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
