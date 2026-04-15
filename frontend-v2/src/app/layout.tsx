import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "cultivOS",
  description: "Inteligencia agricola de precision para Jalisco y Ontario.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="es" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-background text-foreground">
        {children}
      </body>
    </html>
  )
}
