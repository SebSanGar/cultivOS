import type { Metadata } from 'next'
import './globals.css'
import { MainNav } from '@/components/layout/main-nav'
import { Footer } from '@/components/layout/footer'
import { Providers } from '@/components/providers'

export const metadata: Metadata = {
  title: 'cultivOS',
  description: 'Inteligencia agricola de precision para Jalisco y Ontario.',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="es" className="h-full antialiased dark">
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <Providers>
          <MainNav />
          <main className="flex-1">{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  )
}
