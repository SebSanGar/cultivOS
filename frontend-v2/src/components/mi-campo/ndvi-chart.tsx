'use client'

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface NDVIPoint {
  ndvi_mean: number
  analyzed_at: string
}

export function NDVIChart({ data }: { data: NDVIPoint[] }) {
  if (data.length === 0) {
    return (
      <p className="py-4 text-sm text-muted-foreground">
        Sin datos NDVI registrados
      </p>
    )
  }

  const chartData = [...data]
    .sort((a, b) => a.analyzed_at.localeCompare(b.analyzed_at))
    .map((d) => ({
      fecha: new Date(d.analyzed_at).toLocaleDateString('es-MX', {
        day: '2-digit',
        month: 'short',
      }),
      ndvi: parseFloat(d.ndvi_mean.toFixed(3)),
    }))

  return (
    <ResponsiveContainer width="100%" height={120}>
      <AreaChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
        <XAxis
          dataKey="fecha"
          tick={{ fontSize: 10, fill: '#6b7280' }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          domain={[0, 1]}
          tick={{ fontSize: 10, fill: '#6b7280' }}
          tickLine={false}
          axisLine={false}
          tickCount={3}
        />
        <Tooltip
          contentStyle={{
            background: '#111113',
            border: '1px solid #27272a',
            borderRadius: 6,
            fontSize: 12,
            color: '#fafafa',
          }}
          formatter={(v) => [typeof v === 'number' ? v.toFixed(3) : v, 'NDVI']}
          labelStyle={{ color: '#a1a1aa' }}
        />
        <Area
          type="monotone"
          dataKey="ndvi"
          stroke="#22c55e"
          fill="#22c55e"
          fillOpacity={0.15}
          strokeWidth={2}
          dot={chartData.length <= 12}
          activeDot={{ r: 4, fill: '#22c55e' }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
