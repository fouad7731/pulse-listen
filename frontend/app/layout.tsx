import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pulse Listen — Social Listening Sodas & Wellness",
  description: "Veille temps reel Bluesky : volume, sentiment et tendances.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
