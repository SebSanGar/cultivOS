'use client'

import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

interface FarmMapProps {
  lat: number
  lon: number
  farmName: string
}

export function FarmMap({ lat, lon, farmName }: FarmMapProps) {
  return (
    <MapContainer
      center={[lat, lon]}
      zoom={14}
      style={{ height: '12rem', width: '100%', borderRadius: '0.375rem', zIndex: 1 }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <CircleMarker
        center={[lat, lon]}
        radius={10}
        pathOptions={{ color: '#22c55e', fillColor: '#22c55e', fillOpacity: 0.6, weight: 2 }}
      >
        <Popup>{farmName}</Popup>
      </CircleMarker>
    </MapContainer>
  )
}
