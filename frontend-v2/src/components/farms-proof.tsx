"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

interface Farm {
  id: string | number
  name: string
  owner_name?: string
  municipality?: string
  state?: string
  total_hectares?: number
}

export function FarmsProof() {
  const [farms, setFarms] = useState<Farm[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? ""
    fetch(`${apiUrl}/api/farms`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data: Farm[]) => {
        setFarms(data)
        setLoading(false)
      })
      .catch((err: Error) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-5 w-2/3" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-4 w-1/2" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
        Error al cargar granjas: {error}
      </div>
    )
  }

  if (farms.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-muted-foreground">
            No hay granjas registradas todavia.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {farms.map((farm) => (
        <Card key={farm.id}>
          <CardHeader>
            <CardTitle className="text-base">{farm.name}</CardTitle>
          </CardHeader>
          <CardContent>
            {farm.owner_name && (
              <p className="text-sm text-muted-foreground">{farm.owner_name}</p>
            )}
            {(farm.municipality || farm.state) && (
              <p className="text-xs text-muted-foreground">
                {[farm.municipality, farm.state].filter(Boolean).join(", ")}
              </p>
            )}
            {farm.total_hectares != null && (
              <p className="text-xs text-muted-foreground">
                {farm.total_hectares} ha
              </p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
