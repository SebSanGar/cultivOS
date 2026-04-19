import { Suspense } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { CampoClient } from '@/components/mi-campo/campo-client'

function CampoFallback() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 space-y-6">
      <Skeleton className="h-4 w-16" />
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-64" />
      </div>
      <Skeleton className="h-10 w-full rounded-md" />
      <div className="grid gap-4 md:grid-cols-2">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <Skeleton className="h-24 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

export default function MiCampoPage() {
  return (
    <Suspense fallback={<CampoFallback />}>
      <CampoClient />
    </Suspense>
  )
}
