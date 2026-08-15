import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AXON - AI Lab Report Analyzer Dashboard",
  description: "Secure, clinical-grade patient lab report interpreter and conversational companion.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
