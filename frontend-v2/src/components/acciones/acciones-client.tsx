'use client'

import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

const API = process.env.NEXT_PUBLIC_API_URL ?? ''

// ── Types ─────────────────────────────────────────────────────────────

interface Farm {
  id: number
  name: string
  owner_name: string | null
  total_hectares: number
  municipality: string | null
  state: string
}

interface FarmsResponse {
  data: Farm[]
}

interface RecommendationItem {
  field_id: number
  field_name: string
  crop_type: string | null
  health_score: number
  problema: string
  causa_probable: string
  tratamiento: string
  costo_estimado_mxn: number
  urgencia: string
  prevencion: string
  organic: boolean
  metodo_ancestral: string | null
  base_cientifica: string | null
  contexto_regional: string | null
}

interface FarmRecommendationsOut {
  farm_id: number
  farm_name: string
  recommendations: RecommendationItem[]
}

interface MilestoneOut {
  name: string
  achieved: boolean
  achieved_at: string | null
  description_es: string
}

interface FarmRegenMilestonesOut {
  farm_id: number
  milestones: MilestoneOut[]
  milestones_achieved_count: number
  next_milestone_es: string
  progress_to_next_pct: number
}

// ── Fetchers ──────────────────────────────────────────────────────────

async function fetchFarms(): Promise<FarmsResponse> {
  const res = await fetch(`${API}/api/farms?page_size=100`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchRecommendations(farmId: number): Promise<FarmRecommendationsOut> {
  const res = await fetch(`${API}/api/farms/${farmId}/recommendations`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchRegenMilestones(farmId: number): Promise<FarmRegenMilestonesOut> {
  const res = await fetch(`${API}/api/farms/${farmId}/regen-milestones`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// ── Helpers ───────────────────────────────────────────────────────────

function urgenciaBadge(urgencia: string) {
  if (urgencia === 'alta') return 'bg-red-600 text-white hover:bg-red-600'
  if (urgencia === 'media') return 'bg-yellow-500 text-black hover:bg-yellow-500'
  return 'bg-muted text-muted-foreground hover:bg-muted'
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
        <h1 className="text-2xl font-bold tracking-tight">Acciones</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Elige una granja para ver sus recomendaciones y scorecard regenerativo.
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
              href={`/acciones?farm=${farm.id}`}
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

// ── Recommendation card ───────────────────────────────────────────────

function RecoCard({
  reco,
  onDone,
}: {
  reco: RecommendationItem
  onDone: () => void
}) {
  const tooltipBody = [
    reco.causa_probable && `Causa: ${reco.causa_probable}`,
    reco.base_cientifica && `Base: ${reco.base_cientifica}`,
    reco.metodo_ancestral && `Metodo ancestral: ${reco.metodo_ancestral}`,
    reco.prevencion && `Prevencion: ${reco.prevencion}`,
    reco.contexto_regional && `Region: ${reco.contexto_regional}`,
  ]
    .filter(Boolean)
    .join('\n')

  return (
    <Card>
      <CardContent className="pt-5 pb-4 space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-0.5 min-w-0">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <p className="font-semibold text-base leading-snug cursor-default">
                    {reco.tratamiento}
                  </p>
                </TooltipTrigger>
                {tooltipBody && (
                  <TooltipContent side="bottom" className="max-w-xs whitespace-pre-line text-xs">
                    {tooltipBody}
                  </TooltipContent>
                )}
              </Tooltip>
            </TooltipProvider>
            <p className="text-sm text-muted-foreground">{reco.problema}</p>
          </div>
          <Badge className={`shrink-0 capitalize ${urgenciaBadge(reco.urgencia)}`}>
            {reco.urgencia}
          </Badge>
        </div>

        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2 flex-wrap text-xs text-muted-foreground">
            <span>{reco.field_name}</span>
            {reco.crop_type && <span>· {reco.crop_type}</span>}
            {reco.costo_estimado_mxn > 0 && (
              <span>· ${reco.costo_estimado_mxn.toLocaleString('es-MX')} MXN</span>
            )}
            {reco.organic && (
              <Badge variant="outline" className="text-xs py-0 h-5">
                Organico
              </Badge>
            )}
          </div>
          <Button size="sm" variant="outline" onClick={onDone}>
            Marcar hecho
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

// ── Regen scorecard ───────────────────────────────────────────────────

function RegenScorecard({ farmId }: { farmId: number }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['regen-milestones', farmId],
    queryFn: () => fetchRegenMilestones(farmId),
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-16 w-full rounded-lg" />
        ))}
      </div>
    )
  }

  if (isError || !data) {
    return (
      <Card>
        <CardContent className="py-6 text-center text-sm text-muted-foreground">
          Sin datos de scorecard regenerativo para esta granja.
        </CardContent>
      </Card>
    )
  }

  const achieved = data.milestones_achieved_count
  const total = data.milestones.length

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium">
            {achieved} de {total} logros alcanzados
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Proximo: {data.next_milestone_es}
          </p>
        </div>
        <Badge variant="secondary" className="tabular-nums">
          {Math.round(data.progress_to_next_pct)}%
        </Badge>
      </div>

      {/* Progress bar toward next milestone */}
      <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full bg-primary transition-all duration-500"
          style={{ width: `${Math.min(100, data.progress_to_next_pct)}%` }}
        />
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {data.milestones.map((m) => (
          <div
            key={m.name}
            className={`rounded-lg border p-3 space-y-1 ${
              m.achieved
                ? 'border-green-600/40 bg-green-950/20'
                : 'border-border bg-card opacity-60'
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium leading-snug">{m.name}</p>
              {m.achieved && (
                <span className="text-xs text-green-500 shrink-0">Logrado</span>
              )}
            </div>
            <p className="text-xs text-muted-foreground leading-snug">{m.description_es}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Recommendations sections ──────────────────────────────────────────

function AccionesDetail({ farmId }: { farmId: number }) {
  const [done, setDone] = useState<Set<string>>(new Set())

  const { data, isLoading, isError } = useQuery({
    queryKey: ['recommendations', farmId],
    queryFn: () => fetchRecommendations(farmId),
  })

  const allRecos = (data?.recommendations ?? []).filter(
    (r) => !done.has(`${r.field_id}-${r.tratamiento}`),
  )
  const altaRecos = allRecos.filter((r) => r.urgencia === 'alta')
  const mediaRecos = allRecos.filter((r) => r.urgencia === 'media')
  const bajaRecos = allRecos.filter((r) => r.urgencia === 'baja')

  function markDone(reco: RecommendationItem) {
    setDone((prev) => new Set(prev).add(`${reco.field_id}-${reco.tratamiento}`))
  }

  function RecoList({ items }: { items: RecommendationItem[] }) {
    if (items.length === 0) {
      return (
        <Card>
          <CardContent className="py-8 text-center text-sm text-muted-foreground">
            Sin recomendaciones en esta categoria.
          </CardContent>
        </Card>
      )
    }
    return (
      <div className="space-y-3">
        {items.map((reco, i) => (
          <RecoCard key={i} reco={reco} onDone={() => markDone(reco)} />
        ))}
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 space-y-8">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <Link
            href="/acciones"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            &larr; Acciones
          </Link>
          <h1 className="mt-2 text-2xl font-bold tracking-tight">
            {data?.farm_name ?? <Skeleton className="inline-block h-7 w-40" />}
          </h1>
        </div>
      </div>

      {/* Prioridad alta */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold">Prioridad alta</h2>
          {!isLoading && (
            <Badge className="bg-red-600 text-white hover:bg-red-600 tabular-nums">
              {altaRecos.length}
            </Badge>
          )}
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <Skeleton key={i} className="h-28 w-full rounded-lg" />
            ))}
          </div>
        ) : isError ? (
          <Card>
            <CardContent className="py-6 text-center text-sm text-destructive">
              Error al cargar recomendaciones.
            </CardContent>
          </Card>
        ) : altaRecos.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center space-y-1">
              <p className="text-sm font-medium">Todo en orden</p>
              <p className="text-xs text-muted-foreground">
                Sin acciones urgentes para esta granja.
              </p>
            </CardContent>
          </Card>
        ) : (
          <RecoList items={altaRecos} />
        )}
      </section>

      {/* Scorecard regenerativo */}
      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Scorecard regenerativo</h2>
        <RegenScorecard farmId={farmId} />
      </section>

      {/* Historial */}
      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Historial de recomendaciones</h2>

        <Tabs defaultValue="activas">
          <TabsList>
            <TabsTrigger value="activas">
              Activas
              {!isLoading && (
                <span className="ml-1.5 text-xs text-muted-foreground tabular-nums">
                  ({allRecos.length})
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="media">Media prioridad</TabsTrigger>
            <TabsTrigger value="baja">Baja prioridad</TabsTrigger>
            <TabsTrigger value="completadas">Completadas</TabsTrigger>
          </TabsList>

          <TabsContent value="activas" className="mt-4">
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-24 w-full rounded-lg" />
                ))}
              </div>
            ) : (
              <RecoList items={allRecos} />
            )}
          </TabsContent>

          <TabsContent value="media" className="mt-4">
            <RecoList items={mediaRecos} />
          </TabsContent>

          <TabsContent value="baja" className="mt-4">
            <RecoList items={bajaRecos} />
          </TabsContent>

          <TabsContent value="completadas" className="mt-4">
            {done.size === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-sm text-muted-foreground">
                  Marca recomendaciones como hechas y apareceran aqui.
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="py-6 text-center space-y-1">
                  <p className="text-sm font-medium">{done.size} accion(es) completada(s)</p>
                  <p className="text-xs text-muted-foreground">
                    Se restablecen al recargar la pagina.
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </section>
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────

export function AccionesClient() {
  const searchParams = useSearchParams()
  const farmParam = searchParams.get('farm')
  const farmId = farmParam ? parseInt(farmParam, 10) : null

  if (!farmId || isNaN(farmId)) {
    return <FarmPicker />
  }

  return <AccionesDetail farmId={farmId} />
}
