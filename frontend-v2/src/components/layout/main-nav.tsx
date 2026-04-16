'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from '@/components/ui/navigation-menu'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { label: 'Granjas', href: '/' },
  { label: 'Mi Campo', href: '/mi-campo' },
  { label: 'Acciones', href: '/acciones' },
  { label: 'Sabiduría', href: '/sabiduria' },
  { label: 'Sistema', href: '/sistema' },
] as const

export function MainNav() {
  const pathname = usePathname()

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link
          href="/"
          className="text-lg font-bold tracking-tight focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-sm"
        >
          cultivOS
        </Link>

        <NavigationMenu>
          <NavigationMenuList>
            {NAV_ITEMS.map(({ label, href }) => {
              const isActive =
                href === '/' ? pathname === '/' : pathname.startsWith(href)

              return (
                <NavigationMenuItem key={href}>
                  <NavigationMenuLink asChild active={isActive}>
                    <Link
                      href={href}
                      aria-current={isActive ? 'page' : undefined}
                      className={cn(navigationMenuTriggerStyle())}
                    >
                      {label}
                    </Link>
                  </NavigationMenuLink>
                </NavigationMenuItem>
              )
            })}
          </NavigationMenuList>
        </NavigationMenu>
      </div>
    </header>
  )
}
