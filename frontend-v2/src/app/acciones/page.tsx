import { Suspense } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { AccionesClient } from '@/components/acciones/acciones-client'

function AccionesFallback() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 space-y-6">
      <Skeleton className="h-4 w-16" />
      <Skeleton className="h-8 w-48" />
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardContent className="pt-5">
              <Skeleton className="h-20 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

export default function AccionesPage() {
  return (
    <Suspense fallback={<AccionesFallback />}>
      <AccionesClient />
    </Suspense>
  )
}
