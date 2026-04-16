import Link from 'next/link'

export function Footer() {
  return (
    <footer className="mt-auto border-t border-border">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4 text-sm text-muted-foreground">
        <span className="font-semibold text-foreground">cultivOS</span>
        <span>Agricultura de precisión para Jalisco</span>
        <Link
          href="/sistema"
          className="hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-sm"
        >
          Sistema
        </Link>
      </div>
    </footer>
  )
}
