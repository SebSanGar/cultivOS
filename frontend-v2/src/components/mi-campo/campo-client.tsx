'use client'

import dynamic from 'next/dynamic'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { NDVIChart } from './ndvi-chart'

const API = process.env.NEXT_PUBLIC_API_URL ?? ''

const FarmMap = dynamic(
  () => import('./farm-map').then((m) => m.FarmMap),
  { ssr: false, loading: () => <Skeleton className="h-48 w-full rounded-md" /> },
)

// ── Types ─────────────────────────────────────────────────────────────

interface Farm {
  id: number
  name: string
  owner_name: string | null
  location_lat: number | null
  location_lon: number | null
  total_hectares: number
  municipality: string | null
  state: string
  country: string
}

interface FarmsResponse {
  data: Farm[]
}

interface Field {
  id: number
  farm_id: number
  name: string
  crop_type: string | null
  hectares: number
  planted_at: string | null
}

interface HealthScore {
  id: number
  field_id: number
  score: number
  ndvi_mean: number | null
  stress_pct: number | null
  trend: string | null
  sources: string[]
  breakdown: Record<string, number>
  scored_at: string
}

interface NDVIResult {
  id: number
  field_id: number
  ndvi_mean: number
  analyzed_at: string
}

interface SoilAnalysis {
  id: number
  field_id: number
  ph: number | null
  organic_matter_pct: number | null
  nitrogen_ppm: number | null
  phosphorus_ppm: number | null
  potassium_ppm: number | null
  texture: string | null
  moisture_pct: number | null
  sampled_at: string
}

interface RecommendationItem {
  field_id: number
  field_name: string
  crop_type: string | null
  health_score: number
  problema: string
  tratamiento: string
  urgencia: string
  organic: boolean
}

// ── Fetchers ──────────────────────────────────────────────────────────

async function fetchFarms(): Promise<FarmsResponse> {
  const res = await fetch(`${API}/api/farms?page_size=100`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchFarm(farmId: number): Promise<Farm> {
  const res = await fetch(`${API}/api/farms/${farmId}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchFields(farmId: number): Promise<Field[]> {
  const res = await fetch(`${API}/api/farms/${farmId}/fields`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchHealth(farmId: number, fieldId: number): Promise<HealthScore[]> {
  const res = await fetch(`${API}/api/farms/${farmId}/fields/${fieldId}/health`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchNDVI(farmId: number, fieldId: number): Promise<NDVIResult[]> {
  const res = await fetch(`${API}/api/farms/${farmId}/fields/${fieldId}/ndvi`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchSoil(farmId: number, fieldId: number): Promise<SoilAnalysis[]> {
  const res = await fetch(`${API}/api/farms/${farmId}/fields/${fieldId}/soil`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchRecommendations(
  farmId: number,
): Promise<{ recommendations: RecommendationItem[] }> {
  const res = await fetch(`${API}/api/farms/${farmId}/recommendations`)
  if (!res.ok) return { recommendations: [] }
  return res.json()
}

// ── Helpers ───────────────────────────────────────────────────────────

function healthColor(score: number) {
  if (score >= 80) return { badge: 'bg-green-600 text-white hover:bg-green-600', label: 'Saludable' }
  if (score >= 60) return { badge: 'bg-yellow-500 text-black hover:bg-yellow-500', label: 'Moderado' }
  if (score >= 40) return { badge: 'bg-orange-500 text-white hover:bg-orange-500', label: 'Estrés' }
  return { badge: 'bg-red-600 text-white hover:bg-red-600', label: 'Critico' }
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString('es-MX', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

// ── Farm picker ───────────────────────────────────────────────────────

function FarmPicker() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['farms'],
    queryFn: fetchFarms,
  })
  const farms = data?.data ?? []

  return (
    <div className="mx-auto max-w-2xl px-4 py-12 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Mi Campo</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Elige una granja para ver el detalle de sus parcelas.
        </p>
      </div>

      {isLoading && (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      )}

      {isError && (
        <p className="text-sm text-destructive">Error al cargar granjas.</p>
      )}

      {!isLoading && farms.length === 0 && !isError && (
        <Card>
          <CardContent className="py-10 text-center space-y-3">
            <p className="text-muted-foreground text-sm">No hay granjas registradas.</p>
            <Button asChild variant="outline" size="sm">
              <Link href="/">Ir a Granjas</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {farms.length > 0 && (
        <div className="space-y-2">
          {farms.map((farm) => (
            <Link
              key={farm.id}
              href={`/mi-campo?farm=${farm.id}`}
              className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3 hover:border-primary/50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <div>
                <p className="font-medium text-sm">{farm.name}</p>
                {farm.owner_name && (
                  <p className="text-xs text-muted-foreground">{farm.owner_name}</p>
                )}
              </div>
              <Badge variant="secondary" className="shrink-0">
                {farm.total_hectares.toFixed(1)} ha
              </Badge>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Per-field section components ──────────────────────────────────────

function FieldSaludCard({ farmId, field }: { farmId: number; field: Field }) {
  const { data: scores, isLoading } = useQuery({
    queryKey: ['health', farmId, field.id],
    queryFn: () => fetchHealth(farmId, field.id),
  })

  const latest = scores?.[0]

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-10 w-24" />
        </CardContent>
      </Card>
    )
  }

  if (!latest) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">{field.name}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Sin datos de salud</p>
        </CardContent>
      </Card>
    )
  }

  const { badge, label } = healthColor(latest.score)

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-sm font-medium">{field.name}</CardTitle>
          <Badge className={badge}>{label}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-1">
        <p className="text-3xl font-bold tabular-nums">
          {latest.score.toFixed(0)}
          <span className="ml-1 text-base font-normal text-muted-foreground">/ 100</span>
        </p>
        {latest.trend && (
          <p className="text-xs text-muted-foreground capitalize">
            Tendencia: {latest.trend.replace('_', ' ')}
          </p>
        )}
        {latest.ndvi_mean != null && (
          <p className="text-xs text-muted-foreground">NDVI: {latest.ndvi_mean.toFixed(3)}</p>
        )}
        <p className="text-xs text-muted-foreground">{fmtDate(latest.scored_at)}</p>
      </CardContent>
    </Card>
  )
}

function FieldNDVICard({ farmId, field }: { farmId: number; field: Field }) {
  const { data: results, isLoading } = useQuery({
    queryKey: ['ndvi', farmId, field.id],
    queryFn: () => fetchNDVI(farmId, field.id),
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-28 w-full" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">{field.name}</CardTitle>
          {results && results.length > 0 && (
            <span className="text-xs text-muted-foreground">{results.length} lecturas</span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <NDVIChart data={results ?? []} />
      </CardContent>
    </Card>
  )
}

function FieldSueloCard({ farmId, field }: { farmId: number; field: Field }) {
  const { data: analyses, isLoading } = useQuery({
    queryKey: ['soil', farmId, field.id],
    queryFn: () => fetchSoil(farmId, field.id),
  })

  const latest = analyses?.[0]

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    )
  }

  if (!latest) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">{field.name}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Sin analisis de suelo</p>
        </CardContent>
      </Card>
    )
  }

  const rows: { label: string; value: string }[] = [
    latest.ph != null && { label: 'pH', value: latest.ph.toFixed(1) },
    latest.organic_matter_pct != null && {
      label: 'Materia organica',
      value: `${latest.organic_matter_pct.toFixed(1)}%`,
    },
    latest.nitrogen_ppm != null && {
      label: 'Nitrogeno',
      value: `${latest.nitrogen_ppm.toFixed(0)} ppm`,
    },
    latest.phosphorus_ppm != null && {
      label: 'Fosforo',
      value: `${latest.phosphorus_ppm.toFixed(0)} ppm`,
    },
    latest.potassium_ppm != null && {
      label: 'Potasio',
      value: `${latest.potassium_ppm.toFixed(0)} ppm`,
    },
    latest.texture != null && { label: 'Textura', value: latest.texture },
    latest.moisture_pct != null && {
      label: 'Humedad',
      value: `${latest.moisture_pct.toFixed(1)}%`,
    },
  ].filter(Boolean) as { label: string; value: string }[]

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">{field.name}</CardTitle>
          <span className="text-xs text-muted-foreground">{fmtDate(latest.sampled_at)}</span>
        </div>
      </CardHeader>
      <CardContent>
        <table className="w-full text-sm">
          <tbody>
            {rows.map(({ label, value }) => (
              <tr key={label} className="border-b border-border/50 last:border-0">
                <td className="py-1 text-muted-foreground">{label}</td>
                <td className="py-1 text-right font-medium tabular-nums">{value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  )
}

// ── Field grid loader (used when fields are loading) ──────────────────

function FieldGridSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {[1, 2].map((i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <Skeleton className="h-4 w-32" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-24 w-full" />
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function EmptyFields() {
  return (
    <Card>
      <CardContent className="py-8 text-center text-sm text-muted-foreground">
        Sin parcelas en esta granja.
      </CardContent>
    </Card>
  )
}

// ── Farm detail ───────────────────────────────────────────────────────

function FarmDetail({ farmId }: { farmId: number }) {
  const farmQuery = useQuery({
    queryKey: ['farm', farmId],
    queryFn: () => fetchFarm(farmId),
  })

  const fieldsQuery = useQuery({
    queryKey: ['fields', farmId],
    queryFn: () => fetchFields(farmId),
  })

  const recoQuery = useQuery({
    queryKey: ['recommendations', farmId],
    queryFn: () => fetchRecommendations(farmId),
  })

  const farm = farmQuery.data
  const fields = fieldsQuery.data ?? []
  const topRecos = (recoQuery.data?.recommendations ?? []).slice(0, 3)

  if (farmQuery.isError) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-12 space-y-4">
        <p className="text-sm text-destructive">
          Error al cargar granja: {(farmQuery.error as Error).message}
        </p>
        <Button asChild variant="outline" size="sm">
          <Link href="/mi-campo">Volver</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 space-y-6">
      <Link
        href="/mi-campo"
        className="text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        &larr; Granjas
      </Link>

      {farmQuery.isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
      ) : farm ? (
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{farm.name}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {[
              farm.owner_name,
              [farm.municipality, farm.state].filter(Boolean).join(', '),
              `${farm.total_hectares.toFixed(1)} ha`,
            ]
              .filter(Boolean)
              .join(' · ')}
          </p>
        </div>
      ) : null}

      <Tabs defaultValue="portada">
        <TabsList className="w-full justify-start flex-wrap gap-y-1 h-auto">
          <TabsTrigger value="portada">Portada</TabsTrigger>
          <TabsTrigger value="salud">Salud</TabsTrigger>
          <TabsTrigger value="ndvi">NDVI</TabsTrigger>
          <TabsTrigger value="suelo">Suelo</TabsTrigger>
          <TabsTrigger value="recomendaciones">Acciones</TabsTrigger>
        </TabsList>

        {/* Portada */}
        <TabsContent value="portada" className="mt-4">
          {farmQuery.isLoading ? (
            <div className="grid gap-4 md:grid-cols-2">
              <Skeleton className="h-48 w-full rounded-md" />
              <Skeleton className="h-48 w-full rounded-md" />
            </div>
          ) : farm ? (
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardContent className="pt-6">
                  <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                    {[
                      ['Propietario', farm.owner_name ?? '—'],
                      ['Hectareas', `${farm.total_hectares.toFixed(1)} ha`],
                      ['Municipio', farm.municipality ?? '—'],
                      ['Estado', farm.state],
                      ['Pais', farm.country === 'CA' ? 'Canada' : 'Mexico'],
                      [
                        'Parcelas',
                        fieldsQuery.isLoading ? '...' : String(fields.length),
                      ],
                    ].map(([label, value]) => (
                      <div key={label}>
                        <dt className="text-xs text-muted-foreground uppercase tracking-wide">
                          {label}
                        </dt>
                        <dd className="font-medium mt-0.5">{value}</dd>
                      </div>
                    ))}
                  </dl>
                </CardContent>
              </Card>

              {farm.location_lat != null && farm.location_lon != null ? (
                <FarmMap
                  lat={farm.location_lat}
                  lon={farm.location_lon}
                  farmName={farm.name}
                />
              ) : (
                <div className="h-48 w-full rounded-md border border-border flex items-center justify-center bg-muted/30">
                  <p className="text-sm text-muted-foreground">Sin coordenadas registradas</p>
                </div>
              )}
            </div>
          ) : null}
        </TabsContent>

        {/* Salud */}
        <TabsContent value="salud" className="mt-4">
          {fieldsQuery.isLoading ? (
            <FieldGridSkeleton />
          ) : fields.length === 0 ? (
            <EmptyFields />
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {fields.map((field) => (
                <FieldSaludCard key={field.id} farmId={farmId} field={field} />
              ))}
            </div>
          )}
        </TabsContent>

        {/* NDVI */}
        <TabsContent value="ndvi" className="mt-4">
          {fieldsQuery.isLoading ? (
            <FieldGridSkeleton />
          ) : fields.length === 0 ? (
            <EmptyFields />
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {fields.map((field) => (
                <FieldNDVICard key={field.id} farmId={farmId} field={field} />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Suelo */}
        <TabsContent value="suelo" className="mt-4">
          {fieldsQuery.isLoading ? (
            <FieldGridSkeleton />
          ) : fields.length === 0 ? (
            <EmptyFields />
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {fields.map((field) => (
                <FieldSueloCard key={field.id} farmId={farmId} field={field} />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Recomendaciones */}
        <TabsContent value="recomendaciones" className="mt-4 space-y-3">
          {recoQuery.isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-24 w-full rounded-lg" />
              ))}
            </div>
          ) : topRecos.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center space-y-1">
                <p className="text-sm text-muted-foreground">
                  Sin recomendaciones disponibles.
                </p>
                <p className="text-xs text-muted-foreground">
                  Se necesitan datos de salud para generar acciones.
                </p>
              </CardContent>
            </Card>
          ) : (
            topRecos.map((reco, i) => (
              <Card key={i}>
                <CardContent className="pt-5 pb-4 space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-semibold text-sm leading-snug">{reco.tratamiento}</p>
                    <Badge
                      variant={reco.urgencia === 'alta' ? 'destructive' : 'secondary'}
                      className="shrink-0 capitalize"
                    >
                      {reco.urgencia}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{reco.problema}</p>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs text-muted-foreground">{reco.field_name}</span>
                    {reco.crop_type && (
                      <span className="text-xs text-muted-foreground">· {reco.crop_type}</span>
                    )}
                    {reco.organic && (
                      <Badge variant="outline" className="text-xs py-0 h-5">
                        Organico
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────

export function CampoClient() {
  const searchParams = useSearchParams()
  const farmParam = searchParams.get('farm')
  const farmId = farmParam ? parseInt(farmParam, 10) : null

  if (!farmId || isNaN(farmId)) {
    return <FarmPicker />
  }

  return <FarmDetail farmId={farmId} />
}
