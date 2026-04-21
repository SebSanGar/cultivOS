import { Suspense } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { SabiduríaClient } from '@/components/sabiduria/sabiduria-client'

function SabiduríaFallback() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-8 space-y-6">
      <div className="space-y-1">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-4 w-96" />
      </div>
      <Skeleton className="h-10 w-80" />
      <div className="flex gap-2">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-9 w-36 rounded-md" />
        ))}
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i}>
            <CardContent className="pt-5 space-y-2">
              <Skeleton className="h-5 w-2/3" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-4/5" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

export default function SabiduríaPage() {
  return (
    <Suspense fallback={<SabiduríaFallback />}>
      <SabiduríaClient />
    </Suspense>
  )
}
