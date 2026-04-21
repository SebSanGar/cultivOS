'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

const API = process.env.NEXT_PUBLIC_API_URL ?? ''

// ── Types ─────────────────────────────────────────────────────────────

interface AncestralMethod {
  id: number
  name: string
  description_es: string
  region: string
  practice_type: string
  crops: string[]
  benefits_es: string
  scientific_basis: string | null
  problems: string[]
}

interface CropType {
  id: number
  name: string
  family: string
  growing_season: string
  water_needs: string
  regions: string[]
  companions: string[]
  days_to_harvest: number | null
  description_es: string
}

interface Fertilizer {
  id: number
  name: string
  description_es: string
  application_method: string
  cost_per_ha_mxn: number
  nutrient_profile: string
  suitable_crops: string[]
}

interface AgronomistTip {
  id: number
  crop: string
  problem: string
  tip_text_es: string
  source: string | null
  region: string | null
  season: string | null
}

// ── Fetchers ──────────────────────────────────────────────────────────

async function fetchAncestral(): Promise<AncestralMethod[]> {
  const res = await fetch(`${API}/api/knowledge/ancestral`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchCrops(): Promise<CropType[]> {
  const res = await fetch(`${API}/api/knowledge/crops`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchFertilizers(): Promise<Fertilizer[]> {
  const res = await fetch(`${API}/api/knowledge/fertilizers`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchTips(): Promise<AgronomistTip[]> {
  const res = await fetch(`${API}/api/knowledge/agronomist-tips`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// ── Helpers ───────────────────────────────────────────────────────────

function normalize(s: string) {
  return s
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
}

function matches(term: string, ...fields: (string | null | undefined)[]) {
  const t = normalize(term)
  return fields.some((f) => f && normalize(f).includes(t))
}

// ── Loading skeleton ──────────────────────────────────────────────────

function CardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-2/3" />
      </CardHeader>
      <CardContent className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-4/5" />
        <div className="flex gap-1 pt-1">
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="h-5 w-20 rounded-full" />
        </div>
      </CardContent>
    </Card>
  )
}

function LoadingGrid() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <Card>
      <CardContent className="py-10 text-center text-sm text-muted-foreground">
        {message}
      </CardContent>
    </Card>
  )
}

function ErrorState() {
  return (
    <Card>
      <CardContent className="py-10 text-center text-sm text-destructive">
        Error al cargar datos. Verifica la conexion con la API.
      </CardContent>
    </Card>
  )
}

// ── Tab: Ancestral ────────────────────────────────────────────────────

function AncestralTab({ search }: { search: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['knowledge-ancestral'],
    queryFn: fetchAncestral,
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) return <LoadingGrid />
  if (isError || !data) return <ErrorState />

  const items = search
    ? data.filter((m) =>
        matches(search, m.name, m.description_es, m.region, m.practice_type, m.benefits_es)
      )
    : data

  if (items.length === 0) return <EmptyState message="Sin resultados para esa busqueda." />

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((m) => (
        <Card key={m.id} className="flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-base leading-snug">{m.name}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 flex-1">
            <p className="text-sm text-muted-foreground leading-relaxed">{m.description_es}</p>

            {m.benefits_es && (
              <p className="text-xs text-muted-foreground border-l-2 border-primary/30 pl-2">
                {m.benefits_es}
              </p>
            )}

            <div className="flex flex-wrap gap-1 mt-auto pt-1">
              <Badge variant="secondary" className="text-xs">
                {m.region}
              </Badge>
              <Badge variant="outline" className="text-xs capitalize">
                {m.practice_type.replace(/_/g, ' ')}
              </Badge>
              {m.scientific_basis ? (
                <Badge className="text-xs bg-green-800/60 text-green-200 hover:bg-green-800/60 border-0">
                  Validado
                </Badge>
              ) : (
                <Badge variant="outline" className="text-xs text-muted-foreground">
                  Tradicional
                </Badge>
              )}
            </div>

            {m.crops.length > 0 && (
              <p className="text-xs text-muted-foreground">
                Cultivos: {m.crops.join(', ')}
              </p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// ── Tab: Cultivos ─────────────────────────────────────────────────────

function CultivosTab({ search }: { search: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['knowledge-crops'],
    queryFn: fetchCrops,
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) return <LoadingGrid />
  if (isError || !data) return <ErrorState />

  const items = search
    ? data.filter((c) =>
        matches(search, c.name, c.description_es, c.family, c.growing_season, ...c.regions)
      )
    : data

  if (items.length === 0) return <EmptyState message="Sin resultados para esa busqueda." />

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((c) => (
        <Card key={c.id} className="flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-base leading-snug capitalize">{c.name}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 flex-1">
            <p className="text-sm text-muted-foreground leading-relaxed">{c.description_es}</p>

            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground">
              <span>Familia: <span className="text-foreground">{c.family}</span></span>
              <span>Agua: <span className="text-foreground">{c.water_needs}</span></span>
              {c.days_to_harvest && (
                <span>Cosecha: <span className="text-foreground">{c.days_to_harvest} dias</span></span>
              )}
              <span>Ciclo: <span className="text-foreground">{c.growing_season}</span></span>
            </div>

            <div className="flex flex-wrap gap-1 mt-auto pt-1">
              {c.regions.map((r) => (
                <Badge key={r} variant="secondary" className="text-xs capitalize">
                  {r}
                </Badge>
              ))}
            </div>

            {c.companions.length > 0 && (
              <p className="text-xs text-muted-foreground">
                Companeros: {c.companions.join(', ')}
              </p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// ── Tab: Fertilizantes ────────────────────────────────────────────────

function FertilizantesTab({ search }: { search: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['knowledge-fertilizers'],
    queryFn: fetchFertilizers,
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) return <LoadingGrid />
  if (isError || !data) return <ErrorState />

  const items = search
    ? data.filter((f) =>
        matches(
          search,
          f.name,
          f.description_es,
          f.nutrient_profile,
          f.application_method,
          ...f.suitable_crops
        )
      )
    : data

  if (items.length === 0) return <EmptyState message="Sin resultados para esa busqueda." />

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((f) => (
        <Card key={f.id} className="flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-base leading-snug">{f.name}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 flex-1">
            <p className="text-sm text-muted-foreground leading-relaxed">{f.description_es}</p>

            <div className="text-xs text-muted-foreground space-y-0.5">
              <p>Aplicacion: <span className="text-foreground">{f.application_method}</span></p>
              <p>Perfil: <span className="text-foreground">{f.nutrient_profile}</span></p>
              <p>
                Costo:{' '}
                <span className="text-foreground">
                  ${f.cost_per_ha_mxn.toLocaleString('es-MX')} MXN/ha
                </span>
              </p>
            </div>

            {f.suitable_crops.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-auto pt-1">
                {f.suitable_crops.map((crop) => (
                  <Badge key={crop} variant="outline" className="text-xs capitalize">
                    {crop}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// ── Tab: Consejos ─────────────────────────────────────────────────────

function ConsejosTab({ search }: { search: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['knowledge-tips'],
    queryFn: fetchTips,
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) return <LoadingGrid />
  if (isError || !data) return <ErrorState />

  const items = search
    ? data.filter((t) =>
        matches(search, t.tip_text_es, t.crop, t.problem, t.region)
      )
    : data

  if (items.length === 0) return <EmptyState message="Sin resultados para esa busqueda." />

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((t) => (
        <Card key={t.id} className="flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-base leading-snug capitalize">
              {t.crop} — {t.problem.replace(/_/g, ' ')}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 flex-1">
            <p className="text-sm text-muted-foreground leading-relaxed">{t.tip_text_es}</p>

            <div className="flex flex-wrap gap-1 mt-auto pt-1">
              <Badge variant="secondary" className="text-xs capitalize">
                {t.crop}
              </Badge>
              {t.region && (
                <Badge variant="outline" className="text-xs">
                  {t.region}
                </Badge>
              )}
              {t.season && (
                <Badge variant="outline" className="text-xs capitalize">
                  {t.season}
                </Badge>
              )}
            </div>

            {t.source && (
              <p className="text-xs text-muted-foreground">Fuente: {t.source}</p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────

export function SabiduríaClient() {
  const [search, setSearch] = useState('')

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Sabiduría</h1>
        <p className="text-sm text-muted-foreground">
          Biblioteca de referencia: metodos ancestrales, cultivos, fertilizantes y consejos agronomicos para Jalisco.
        </p>
      </div>

      <Input
        type="search"
        placeholder="Buscar por nombre, cultivo, region..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-md"
        aria-label="Buscar en la biblioteca de conocimiento"
      />

      <Tabs defaultValue="ancestral">
        <TabsList className="flex-wrap h-auto gap-1">
          <TabsTrigger value="ancestral">Metodos ancestrales</TabsTrigger>
          <TabsTrigger value="cultivos">Cultivos</TabsTrigger>
          <TabsTrigger value="fertilizantes">Fertilizantes</TabsTrigger>
          <TabsTrigger value="consejos">Consejos agronomicos</TabsTrigger>
        </TabsList>

        <TabsContent value="ancestral" className="mt-6">
          <AncestralTab search={search} />
        </TabsContent>

        <TabsContent value="cultivos" className="mt-6">
          <CultivosTab search={search} />
        </TabsContent>

        <TabsContent value="fertilizantes" className="mt-6">
          <FertilizantesTab search={search} />
        </TabsContent>

        <TabsContent value="consejos" className="mt-6">
          <ConsejosTab search={search} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
