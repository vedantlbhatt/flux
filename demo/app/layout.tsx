import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Flux API Demo",
  description: "Live web search with semantic reranking",
  icons: {
    icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' fill='%2318181b'/><text x='16' y='22' font-size='16' text-anchor='middle' fill='%23fafafa'>F</text></svg>",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}
