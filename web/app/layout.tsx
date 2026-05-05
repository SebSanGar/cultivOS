import type { Metadata } from "next";
import { Geist, Instrument_Serif, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const geist = Geist({
  variable: "--font-sans-stack",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const instrumentSerif = Instrument_Serif({
  variable: "--font-serif-stack",
  subsets: ["latin"],
  weight: ["400"],
  style: ["normal", "italic"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono-stack",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://cultivosagro.com"),
  title: "cultivOS — The Intelligence Layer for Precision Agriculture",
  description:
    "Mexican company digitizing the farmers big agtech wrote off. Drone + AI farm intelligence delivered through the interface each farmer actually uses (WhatsApp in Mexico, dashboard in Canada). Pre-release · Jalisco fieldwork via ITESO partnership · Ontario anchor pilot confirmed at White Church Farm, Haldimand County (400+ ac, expanding).",
  applicationName: "cultivOS",
  keywords: [
    "precision agriculture",
    "agtech",
    "drone agriculture",
    "specialty crops",
    "NDVI",
    "thermal imaging",
    "Mexico agtech",
    "Ontario agtech",
    "Jalisco",
    "smallholder agriculture",
  ],
  authors: [{ name: "cultivOS" }],
  openGraph: {
    title: "cultivOS — The Intelligence Layer for Precision Agriculture",
    description:
      "Hecho en México. We digitize the demographic big agtech wrote off. Drone data → one decision per acre, delivered through the channel each market actually uses.",
    url: "https://cultivosagro.com",
    siteName: "cultivOS",
    locale: "en_CA",
    alternateLocale: ["es_MX"],
    type: "website",
    images: [
      {
        url: "/brand/cultivOS_drop.png",
        width: 1024,
        height: 1024,
        alt: "cultivOS",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "cultivOS — The Intelligence Layer for Precision Agriculture",
    description:
      "Hecho en México. Drone-fed AI brain. One decision per acre, delivered through the channel each market actually uses.",
    images: ["/brand/cultivOS_drop.png"],
  },
  icons: {
    icon: "/brand/cultivOS_drop.png",
    shortcut: "/brand/cultivOS_drop.png",
    apple: "/brand/cultivOS_drop.png",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geist.variable} ${instrumentSerif.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
