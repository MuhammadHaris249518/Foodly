"use client";

import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from "react-leaflet";
import L from "leaflet";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

type Coordinates = {
  lat: number;
  lng: number;
};

type MapPanelProps = {
  selected: Coordinates;
  onSelect: (coords: Coordinates) => void;
};

const DEFAULT_CENTER: [number, number] = [33.6844, 73.0479];

const resolveIconUrl = (icon: string | { src: string }) =>
  typeof icon === "string" ? icon : icon.src;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: resolveIconUrl(markerIcon2x),
  iconUrl: resolveIconUrl(markerIcon),
  shadowUrl: resolveIconUrl(markerShadow),
});

function LocationMarker({ selected, onSelect }: MapPanelProps) {
  useMapEvents({
    click(event) {
      onSelect({ lat: event.latlng.lat, lng: event.latlng.lng });
    },
  });

  return (
    <Marker position={[selected.lat, selected.lng]}>
      <Popup>
        Selected location<br />
        {selected.lat.toFixed(5)}, {selected.lng.toFixed(5)}
      </Popup>
    </Marker>
  );
}

export default function MapPanel({ selected, onSelect }: MapPanelProps) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) {
    return (
      <div className="h-[420px] w-full overflow-hidden rounded-[2rem] border border-slate-100 bg-white shadow-sm flex items-center justify-center text-slate-400">
        Loading map...
      </div>
    );
  }

  return (
    <div className="h-[420px] w-full overflow-hidden rounded-[2rem] border border-slate-100 bg-white shadow-sm">
      <MapContainer center={DEFAULT_CENTER} zoom={13} className="h-full w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <LocationMarker selected={selected} onSelect={onSelect} />
      </MapContainer>
    </div>
  );
}
