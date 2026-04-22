'use client'

import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

const API = process.env.NEXT_PUBLIC_API_URL ?? ''

// ── Types ──────────────────────────────────────────────────────────────

interface AlertHistoryItem {
  id: string
  farm_id: number
  field_id: number | null
  alert_type: string
  message: string
  severity: string
  source: string
  status: string | null
  acknowledged: boolean | null
  created_at: string
}

interface AlertAnalytics {
  total_alerts: number
  total_sms: number
  total_system: number
  delivery_rate: number
  by_severity: Record<string, number>
  farms_reached: number
  fields_reached: number
}

interface PlatformStatus {
  api_version: string
  uptime_seconds: number
  total_farms: number
  total_fields: number
  latest_data: Record<string, string | null>
}

interface SystemHealth {
  status: string
  api_version: string
  python_version: string
  uptime_seconds: number
  database: Record<string, number>
  endpoint_count: number
  test_count: number
}

interface Farm {
  id: number
  name: string
  owner_name: string | null
}

interface FarmsResponse {
  data: Farm[]
}

interface AlertConfig {
  health_score_floor: number
  ndvi_minimum: number
  temp_max_c: number
}

// ── Fetchers ───────────────────────────────────────────────────────────

async function fetchAlertHistory(): Promise<AlertHistoryItem[]> {
  const res = await fetch(`${API}/api/alerts/history`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchAlertAnalytics(): Promise<AlertAnalytics> {
  const res = await fetch(`${API}/api/alerts/analytics`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchStatus(): Promise<PlatformStatus> {
  const res = await fetch(`${API}/api/status`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchSystemHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API}/api/system/health-detailed`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchFarms(): Promise<FarmsResponse> {
  const res = await fetch(`${API}/api/farms?page_size=100`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchAlertConfig(farmId: number): Promise<AlertConfig> {
  const res = await fetch(`${API}/api/farms/${farmId}/alert-config`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// ── Helpers ────────────────────────────────────────────────────────────

function severityClass(severity: string): string {
  if (severity === 'critical') return 'bg-red-600 text-white hover:bg-red-600'
  if (severity === 'warning') return 'bg-yellow-500 text-black hover:bg-yellow-500'
  return 'bg-muted text-muted-foreground hover:bg-muted'
}

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('es-MX', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// ── Shared stat card ───────────────────────────────────────────────────

function StatCard({
  label,
  value,
  valueClass = '',
}: {
  label: string
  value: string
  valueClass?: string
}) {
  return (
    <Card>
      <CardContent className="pt-4 pb-4 space-y-1">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className={`text-2xl font-bold tabular-nums tracking-tight ${valueClass}`}>{value}</p>
      </CardContent>
    </Card>
  )
}

// ── Alertas tab ────────────────────────────────────────────────────────

function AlertasTab() {
  const analytics = useQuery({ queryKey: ['alert-analytics'], queryFn: fetchAlertAnalytics })
  const history = useQuery({ queryKey: ['alert-history'], queryFn: fetchAlertHistory })

  return (
    <div className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-4">
        {analytics.isLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-20 rounded-lg" />
            ))
          : analytics.data
            ? (
                <>
                  <StatCard label="Total alertas" value={String(analytics.data.total_alerts)} />
                  <StatCard
                    label="Tasa de entrega"
                    value={`${analytics.data.delivery_rate.toFixed(1)}%`}
                  />
                  <StatCard
                    label="Granjas con alertas"
                    value={String(analytics.data.farms_reached)}
                  />
                  <StatCard
                    label="Parcelas afectadas"
                    value={String(analytics.data.fields_reached)}
                  />
                </>
              )
            : null}
      </div>

      <div className="space-y-3">
        <h2 className="text-base font-semibold">Historial de alertas</h2>

        {history.isLoading && (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full rounded-lg" />
            ))}
          </div>
        )}

        {history.isError && (
          <Card>
            <CardContent className="py-6 text-center text-sm text-destructive">
              Error al cargar el historial de alertas.
            </CardContent>
          </Card>
        )}

        {history.data && history.data.length === 0 && (
          <Card>
            <CardContent className="py-8 text-center space-y-1">
              <p className="text-sm font-medium">Sin alertas</p>
              <p className="text-xs text-muted-foreground">
                No hay alertas registradas. Cuando el sistema detecte problemas, aparecerán aquí.
              </p>
            </CardContent>
          </Card>
        )}

        {history.data && history.data.length > 0 && (
          <div className="space-y-2">
            {history.data.slice(0, 50).map((item) => (
              <div
                key={item.id}
                className="flex items-start gap-3 rounded-lg border border-border bg-card px-4 py-3"
              >
                <Badge
                  className={`shrink-0 capitalize mt-0.5 ${severityClass(item.severity)}`}
                >
                  {item.severity}
                </Badge>
                <div className="min-w-0 flex-1">
                  <p className="text-sm leading-snug">{item.message}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Granja {item.farm_id}
                    {item.field_id ? ` · Parcela ${item.field_id}` : ''}
                    {' · '}
                    {item.source === 'sms' ? 'SMS' : 'Sistema'}
                    {' · '}
                    {formatDate(item.created_at)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Estado tab ─────────────────────────────────────────────────────────

const DATA_LABELS: Record<string, string> = {
  soil: 'Suelo',
  ndvi: 'NDVI',
  thermal: 'Térmica',
  weather: 'Clima',
}

function EstadoTab() {
  const status = useQuery({ queryKey: ['platform-status'], queryFn: fetchStatus })
  const health = useQuery({ queryKey: ['system-health'], queryFn: fetchSystemHealth })

  return (
    <div className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-3">
        {status.isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-20 rounded-lg" />
            ))
          : status.data
            ? (
                <>
                  <StatCard
                    label="Estado"
                    value="Operativo"
                    valueClass="text-green-400"
                  />
                  <StatCard
                    label="Tiempo activo"
                    value={formatUptime(status.data.uptime_seconds)}
                  />
                  <StatCard label="Versión API" value={status.data.api_version} />
                </>
              )
            : null}
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold">Datos más recientes</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {status.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-5 w-full" />
              ))}
            </div>
          ) : status.data ? (
            <table className="w-full text-sm">
              <tbody className="divide-y divide-border">
                {Object.entries(status.data.latest_data).map(([key, val]) => (
                  <tr key={key}>
                    <td className="py-2 pr-4 text-muted-foreground">
                      {DATA_LABELS[key] ?? key}
                    </td>
                    <td className="py-2 font-mono text-xs">
                      {val ? (
                        formatDate(val)
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </CardContent>
      </Card>

      {health.data && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Base de datos</CardTitle>
          </CardHeader>
          <CardContent className="pt-0 space-y-4">
            <div className="grid gap-2 sm:grid-cols-2">
              {Object.entries(health.data.database).map(([key, count]) => (
                <div
                  key={key}
                  className="flex items-center justify-between rounded bg-muted/40 px-3 py-1.5"
                >
                  <span className="text-xs text-muted-foreground capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <span className="text-sm font-semibold tabular-nums">
                    {count.toLocaleString('es-MX')}
                  </span>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              {health.data.endpoint_count} endpoints · {health.data.test_count} tests · Python{' '}
              {health.data.python_version}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// ── Asistente (3-step onboarding wizard) ──────────────────────────────

const STEPS = [
  {
    title: 'Bienvenido a cultivOS',
    body: 'Inteligencia de precisión para tu campo. Transformamos imágenes de dron en decisiones concretas: cuándo regar, dónde actuar, qué tratar. Diseñado para granjas de Jalisco.',
    cta: 'Comenzar',
    ctaHref: null,
  },
  {
    title: 'Conecta tu primera granja',
    body: 'Ve a Granjas y toca "Cargar datos de ejemplo" para ver el sistema en acción con granjas reales de Jalisco. O toca "+ Nueva Granja" para registrar la tuya.',
    cta: 'Siguiente',
    ctaHref: null,
  },
  {
    title: 'Conoce las 5 áreas',
    body: 'Granjas: tu panel principal. Mi Campo: detalle por parcela (NDVI, suelo, salud). Acciones: qué hacer hoy. Sabiduría: referencia agronómica y métodos ancestrales. Sistema: aquí estás.',
    cta: 'Ir a Granjas',
    ctaHref: '/',
  },
] as const

function AsistenteTab() {
  const [step, setStep] = useState(0)
  const current = STEPS[step]

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div className="flex gap-2">
        {STEPS.map((_, i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
              i <= step ? 'bg-primary' : 'bg-muted'
            }`}
          />
        ))}
      </div>

      <Card>
        <CardContent className="pt-6 pb-6 space-y-4">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground tabular-nums">
              Paso {step + 1} de {STEPS.length}
            </p>
            <h2 className="text-xl font-bold tracking-tight">{current.title}</h2>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">{current.body}</p>

          {current.ctaHref ? (
            <Button asChild className="w-full">
              <Link href={current.ctaHref}>{current.cta}</Link>
            </Button>
          ) : (
            <Button
              className="w-full"
              onClick={() => setStep((s) => Math.min(s + 1, STEPS.length - 1))}
            >
              {current.cta}
            </Button>
          )}

          {step > 0 && !current.ctaHref && (
            <button
              onClick={() => setStep((s) => Math.max(s - 1, 0))}
              className="w-full text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Volver
            </button>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ── Configuración — alert threshold form ───────────────────────────────

function AlertConfigForm({ farmId, farmName }: { farmId: number; farmName: string }) {
  const queryClient = useQueryClient()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['alert-config', farmId],
    queryFn: () => fetchAlertConfig(farmId),
  })

  const [floor, setFloor] = useState('')
  const [ndvi, setNdvi] = useState('')
  const [temp, setTemp] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (data) {
      setFloor(String(data.health_score_floor))
      setNdvi(String(data.ndvi_minimum))
      setTemp(String(data.temp_max_c))
    }
  }, [data])

  const mutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API}/api/farms/${farmId}/alert-config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          health_score_floor: parseFloat(floor),
          ndvi_minimum: parseFloat(ndvi),
          temp_max_c: parseFloat(temp),
        }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return res.json() as Promise<AlertConfig>
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-config', farmId] })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full rounded-lg" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <p className="text-sm text-destructive">Error al cargar la configuración de alertas.</p>
    )
  }

  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <p className="text-sm font-medium">{farmName}</p>
        <p className="text-xs text-muted-foreground">
          Las alertas se disparan cuando los valores caen por debajo de estos umbrales.
        </p>
      </div>

      <div className="space-y-3">
        <div className="space-y-1.5">
          <Label htmlFor="health-floor" className="text-xs">
            Salud mínima (0–100)
          </Label>
          <Input
            id="health-floor"
            type="number"
            min={0}
            max={100}
            value={floor}
            onChange={(e) => setFloor(e.target.value)}
            className="h-9 text-sm"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="ndvi-min" className="text-xs">
            NDVI mínimo (0–1)
          </Label>
          <Input
            id="ndvi-min"
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={ndvi}
            onChange={(e) => setNdvi(e.target.value)}
            className="h-9 text-sm"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="temp-max" className="text-xs">
            Temperatura máxima °C
          </Label>
          <Input
            id="temp-max"
            type="number"
            min={-50}
            max={70}
            value={temp}
            onChange={(e) => setTemp(e.target.value)}
            className="h-9 text-sm"
          />
        </div>
      </div>

      {mutation.isError && (
        <p className="text-xs text-destructive">Error al guardar. Intenta de nuevo.</p>
      )}

      <Button
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending || saved}
        size="sm"
        className="w-full"
      >
        {saved ? 'Guardado' : mutation.isPending ? 'Guardando...' : 'Guardar configuración'}
      </Button>
    </div>
  )
}

// ── Configuración tab ──────────────────────────────────────────────────

function ConfiguracionTab() {
  const [selectedFarm, setSelectedFarm] = useState<{ id: number; name: string } | null>(null)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['farms'],
    queryFn: fetchFarms,
  })
  const farms = data?.data ?? []

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-base font-semibold">Configuración de alertas</h2>
        <p className="text-xs text-muted-foreground">
          Ajusta los umbrales que disparan alertas WhatsApp/SMS por granja.
        </p>
      </div>

      {!selectedFarm ? (
        <div className="space-y-2">
          {isLoading &&
            Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full rounded-lg" />
            ))}

          {isError && (
            <p className="text-sm text-destructive">Error al cargar granjas.</p>
          )}

          {!isLoading && !isError && farms.length === 0 && (
            <Card>
              <CardContent className="py-8 text-center space-y-2">
                <p className="text-sm text-muted-foreground">No hay granjas registradas.</p>
                <Button asChild variant="outline" size="sm">
                  <Link href="/">Ir a Granjas</Link>
                </Button>
              </CardContent>
            </Card>
          )}

          {farms.map((farm) => (
            <button
              key={farm.id}
              onClick={() => setSelectedFarm({ id: farm.id, name: farm.name })}
              className="w-full flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3 hover:border-primary/50 transition-colors text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <div>
                <p className="text-sm font-medium">{farm.name}</p>
                {farm.owner_name && (
                  <p className="text-xs text-muted-foreground">{farm.owner_name}</p>
                )}
              </div>
              <span className="text-xs text-muted-foreground">Configurar &rarr;</span>
            </button>
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          <button
            onClick={() => setSelectedFarm(null)}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            &larr; Cambiar granja
          </button>
          <Card>
            <CardContent className="pt-5 pb-5">
              <AlertConfigForm farmId={selectedFarm.id} farmName={selectedFarm.name} />
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

// ── Main export ────────────────────────────────────────────────────────

export function SistemaClient() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Sistema</h1>
        <p className="text-sm text-muted-foreground">
          Alertas, estado de la plataforma, configuración y guía de inicio.
        </p>
      </div>

      <Tabs defaultValue="alertas">
        <TabsList>
          <TabsTrigger value="alertas">Alertas</TabsTrigger>
          <TabsTrigger value="estado">Estado</TabsTrigger>
          <TabsTrigger value="asistente">Asistente</TabsTrigger>
          <TabsTrigger value="configuracion">Configuración</TabsTrigger>
        </TabsList>

        <TabsContent value="alertas" className="mt-6">
          <AlertasTab />
        </TabsContent>

        <TabsContent value="estado" className="mt-6">
          <EstadoTab />
        </TabsContent>

        <TabsContent value="asistente" className="mt-6">
          <AsistenteTab />
        </TabsContent>

        <TabsContent value="configuracion" className="mt-6">
          <ConfiguracionTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}
