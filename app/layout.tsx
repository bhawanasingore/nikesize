import type { Metadata, Viewport } from "next";
import { product } from "@/lib/product";
import "./globals.css";

export const metadata: Metadata = {
  title: `${product.name} — ${product.colorway}`,
  description: `${product.name} running shoe in ${product.colorway}.`,
};

// Phone layout: fixed to the device width, pinch-zoom turned off.
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
