import { Suspense } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { SistemaClient } from '@/components/sistema/sistema-client'

function SistemaFallback() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 space-y-6">
      <div className="space-y-1">
        <Skeleton className="h-8 w-28" />
        <Skeleton className="h-4 w-80" />
      </div>
      <Skeleton className="h-10 w-96" />
      <div className="grid gap-3 sm:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardContent className="pt-4 pb-4 space-y-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-7 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-16 w-full rounded-lg" />
        ))}
      </div>
    </div>
  )
}

export default function SistemaPage() {
  return (
    <Suspense fallback={<SistemaFallback />}>
      <SistemaClient />
    </Suspense>
  )
}
