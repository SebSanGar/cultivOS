'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const API = process.env.NEXT_PUBLIC_API_URL ?? ''

// ── Types ─────────────────────────────────────────────────────────────

interface Farm {
  id: number
  name: string
  owner_name: string | null
  municipality: string | null
  state: string
  country: string
  total_hectares: number
}

interface FarmsResponse {
  data: Farm[]
  meta: { total: number; page: number; page_size: number }
}

interface PlatformStats {
  total_farms: number
  total_fields: number
  total_hectares: number
  avg_health: number | null
}

// ── Fetchers ──────────────────────────────────────────────────────────

async function fetchFarms(): Promise<FarmsResponse> {
  const res = await fetch(`${API}/api/farms?page_size=100`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function fetchStats(): Promise<PlatformStats> {
  const res = await fetch(`${API}/api/intel/executive-summary`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function postSeedDemo(): Promise<void> {
  const res = await fetch(`${API}/api/demo/seed`, { method: 'POST' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
}

// ── Stat strip ────────────────────────────────────────────────────────

function StatStrip({ stats }: { stats: PlatformStats | undefined }) {
  const cards = [
    {
      label: 'Granjas',
      value: stats ? String(stats.total_farms) : null,
      description: 'registradas en la plataforma',
    },
    {
      label: 'Parcelas',
      value: stats ? String(stats.total_fields) : null,
      description: 'campos monitoreados',
    },
    {
      label: 'Salud promedio',
      value: stats?.avg_health != null ? `${stats.avg_health.toFixed(0)}%` : null,
      description: 'índice de salud de cultivos',
    },
    {
      label: 'Hectáreas',
      value: stats ? stats.total_hectares.toFixed(1) : null,
      description: 'superficie total bajo gestión',
    },
  ]

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.label}>
          <CardContent className="pt-5 pb-4">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              {card.label}
            </p>
            {card.value !== null ? (
              <p className="mt-1 text-3xl font-bold tabular-nums">{card.value}</p>
            ) : (
              <Skeleton className="mt-2 h-8 w-16" />
            )}
            <p className="mt-1 text-xs text-muted-foreground">{card.description}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// ── Farm card ─────────────────────────────────────────────────────────

function FarmCard({ farm }: { farm: Farm }) {
  const location = [farm.municipality, farm.state].filter(Boolean).join(', ')
  const flag = farm.country === 'CA' ? '🇨🇦' : '🇲🇽'

  return (
    <Link href={`/mi-campo?farm=${farm.id}`} className="group block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg">
      <Card className="h-full transition-colors group-hover:border-primary/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-base leading-snug">{farm.name}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          {farm.owner_name && (
            <p className="text-sm text-muted-foreground">{farm.owner_name}</p>
          )}
          <p className="text-xs text-muted-foreground">
            {flag} {location}
          </p>
          <Badge variant="secondary" className="text-xs mt-1">
            {farm.total_hectares.toFixed(1)} ha
          </Badge>
        </CardContent>
      </Card>
    </Link>
  )
}

// ── New farm dialog ───────────────────────────────────────────────────

const EMPTY_FORM = {
  name: '',
  owner_name: '',
  total_hectares: '',
  municipality: '',
  country: 'MX',
}

function NewFarmDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
}) {
  const qc = useQueryClient()
  const [form, setForm] = useState(EMPTY_FORM)

  const mutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API}/api/farms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.name,
          owner_name: form.owner_name || null,
          total_hectares: parseFloat(form.total_hectares) || 0,
          municipality: form.municipality || null,
          country: form.country,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err?.detail ?? `HTTP ${res.status}`)
      }
      return res.json()
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['farms'] })
      qc.invalidateQueries({ queryKey: ['stats'] })
      toast.success('Granja creada correctamente')
      setForm(EMPTY_FORM)
      onOpenChange(false)
    },
    onError: (err: Error) => {
      toast.error(`Error al crear granja: ${err.message}`)
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.name.trim()) return
    mutation.mutate()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Nueva granja</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="farm-name">Nombre *</Label>
            <Input
              id="farm-name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Rancho Las Palmas"
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="farm-owner">Propietario</Label>
            <Input
              id="farm-owner"
              value={form.owner_name}
              onChange={(e) => setForm({ ...form, owner_name: e.target.value })}
              placeholder="Juan García"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="farm-ha">Hectáreas</Label>
            <Input
              id="farm-ha"
              type="number"
              min="0"
              step="0.1"
              value={form.total_hectares}
              onChange={(e) => setForm({ ...form, total_hectares: e.target.value })}
              placeholder="12.5"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="farm-mun">Municipio</Label>
            <Input
              id="farm-mun"
              value={form.municipality}
              onChange={(e) => setForm({ ...form, municipality: e.target.value })}
              placeholder="Tepatitlán"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="farm-country">País</Label>
            <select
              id="farm-country"
              value={form.country}
              onChange={(e) => setForm({ ...form, country: e.target.value })}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="MX">🇲🇽 México</option>
              <option value="CA">🇨🇦 Canadá</option>
            </select>
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={mutation.isPending || !form.name.trim()}>
              {mutation.isPending ? 'Guardando...' : 'Crear granja'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ── Main dashboard ────────────────────────────────────────────────────

export function GranjasDashboard() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const qc = useQueryClient()

  const farmsQuery = useQuery({ queryKey: ['farms'], queryFn: fetchFarms })
  const statsQuery = useQuery({ queryKey: ['stats'], queryFn: fetchStats })

  const seedMutation = useMutation({
    mutationFn: postSeedDemo,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['farms'] })
      qc.invalidateQueries({ queryKey: ['stats'] })
      toast.success('Datos de ejemplo cargados')
    },
    onError: (err: Error) => {
      toast.error(`Error al cargar datos: ${err.message}`)
    },
  })

  const farms = farmsQuery.data?.data ?? []
  const isEmpty = !farmsQuery.isLoading && farms.length === 0

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 space-y-8">
      {/* Header + actions */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Granjas</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Panel de inteligencia agricola
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => seedMutation.mutate()}
            disabled={seedMutation.isPending}
          >
            {seedMutation.isPending ? 'Cargando...' : 'Cargar datos de ejemplo'}
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href="/sistema/onboarding">Asistente guiado</Link>
          </Button>
          <Button size="sm" onClick={() => setDialogOpen(true)}>
            + Nueva Granja
          </Button>
        </div>
      </div>

      {/* Stat strip */}
      <StatStrip stats={statsQuery.data} />

      {/* Farm grid or states */}
      {farmsQuery.isError && (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          Error al cargar granjas: {(farmsQuery.error as Error).message}
        </div>
      )}

      {farmsQuery.isLoading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-2/3" />
              </CardHeader>
              <CardContent className="space-y-2">
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-3 w-1/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {isEmpty && (
        <Card>
          <CardContent className="py-12 text-center space-y-4">
            <p className="text-muted-foreground max-w-sm mx-auto">
              Bienvenido a cultivOS. Toca{' '}
              <span className="font-medium text-foreground">Cargar datos de ejemplo</span>{' '}
              para ver el panel en accion con granjas de Jalisco.
            </p>
            <Button
              onClick={() => seedMutation.mutate()}
              disabled={seedMutation.isPending}
            >
              {seedMutation.isPending ? 'Cargando...' : 'Cargar datos'}
            </Button>
          </CardContent>
        </Card>
      )}

      {!farmsQuery.isLoading && farms.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {farms.map((farm) => (
            <FarmCard key={farm.id} farm={farm} />
          ))}
        </div>
      )}

      <NewFarmDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  )
}
