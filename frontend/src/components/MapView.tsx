import React, { useMemo, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from "react-leaflet";
import type { Facility, LatestReading } from "../types";
import { FUEL_LABELS, carbonColor, ciLabel } from "../types";

import "leaflet/dist/leaflet.css";

interface Props {
  facilities: Facility[];
  latest: LatestReading[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

/**
 * Marker radius scales with √power so large plants don't dominate the map.
 * Range: ~3px (30 MW) to ~14px (3000 MW).
 */
function markerRadius(powerMw: number): number {
  return Math.max(3, Math.min(14, Math.sqrt(powerMw) * 0.4));
}

export default function MapView({ facilities, latest, selectedId, onSelect }: Props) {
  const facMap = useMemo(
    () => new Map(facilities.map((f) => [f.facility_id, f])),
    [facilities],
  );
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const markerLayers = latest.flatMap((d) => {
    const meta = facMap.get(d.facility_id);
    if (!meta) return [];

    const pwr = d.power_mw;
    const em = d.emissions_tco2e;
    const ci = (em * 1000) / Math.max(pwr, 1);
    const ciC = carbonColor(ci);
    const baseR = markerRadius(pwr);

    const isSelected = selectedId === d.facility_id;
    const isHovered = hoveredId === d.facility_id;
    const scale = isSelected ? 1.6 : isHovered ? 1.25 : 1;
    const r = baseR * scale;

    // Glow halo — same color, very low opacity, larger than the dot
    const glowR = r + (isSelected ? 10 : isHovered ? 7 : 5);
    const glowFill = isSelected ? 0.22 : isHovered ? 0.14 : 0.07;

    // White border weight
    const strokeW = isSelected ? 2.5 : isHovered ? 2 : 1.5;

    const kid = d.facility_id;
    const layers: React.ReactNode[] = [];

    // Layer 1: outer glow halo — semi-transparent diffusion ring
    layers.push(
      <CircleMarker
        key={`${kid}-glow`}
        center={[meta.latitude, meta.longitude]}
        radius={glowR}
        pathOptions={{
          color: "transparent",
          fillColor: ciC,
          fillOpacity: glowFill,
          weight: 0,
        }}
        interactive={false}
      />,
    );

    // Layer 2: extra echo ring when selected
    if (isSelected) {
      layers.push(
        <CircleMarker
          key={`${kid}-echo`}
          center={[meta.latitude, meta.longitude]}
          radius={glowR + 7}
          pathOptions={{
            color: "transparent",
            fillColor: ciC,
            fillOpacity: 0.09,
            weight: 0,
          }}
          interactive={false}
        />,
      );
    }

    // Layer 3: main dot — solid fill, crisp white border
    layers.push(
      <CircleMarker
        key={`${kid}-main`}
        center={[meta.latitude, meta.longitude]}
        radius={r}
        pathOptions={{
          color: "white",
          fillColor: ciC,
          fillOpacity: 1,
          weight: strokeW,
        }}
        eventHandlers={{
          click: () => onSelect(d.facility_id),
          mouseover: () => setHoveredId(d.facility_id),
          mouseout: () => setHoveredId(null),
        }}
      >
        <Tooltip direction="top" offset={[0, -r - 4]}>
          <b>{meta.facility_name}</b>
          <br />
          {pwr.toFixed(0)} MW · {ci.toFixed(0)} gCO₂/kWh
        </Tooltip>

        <Popup maxWidth={240}>
          <div className="text-xs min-w-[170px]">
            <div className="font-semibold text-gray-900 text-sm mb-0.5">
              {meta.facility_name}
            </div>
            <div className="text-gray-400 mb-1.5">
              {FUEL_LABELS[meta.fuel_tech] || meta.fuel_tech} · NEM{" "}
              {meta.network_region}
            </div>
            <div className="flex gap-2 mb-1">
              <div className="flex-1 text-center bg-gray-100 rounded py-1 px-1.5">
                <div className="font-semibold text-sm" style={{ color: ciC }}>
                  {ci.toFixed(0)}
                </div>
                <div className="text-[9px] text-gray-400">gCO₂/kWh</div>
              </div>
              <div className="flex-1 text-center bg-gray-100 rounded py-1 px-1.5">
                <div className="font-semibold text-sm text-orange-600">
                  {pwr.toFixed(0)}
                </div>
                <div className="text-[9px] text-gray-400">MW</div>
              </div>
            </div>
            <div className="text-[10px] text-gray-400">
              {ciLabel(ci)} carbon · {d.timestamp?.slice(0, 19)}
            </div>
          </div>
        </Popup>
      </CircleMarker>,
    );

    return layers;
  });

  return (
    <div className="relative w-full h-full">
      <MapContainer
        center={[-33, 145]}
        zoom={5}
        className="w-full h-full"
        zoomControl={true}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />

        {markerLayers}
      </MapContainer>

      {/* Carbon intensity legend */}
      <div className="absolute bottom-6 left-2 z-[1000] glass-card rounded-xl px-2.5 py-2 shadow-sm">
        <div className="text-[9px] text-gray-400 uppercase tracking-wider font-semibold">
          Carbon intensity
        </div>
        <div className="text-[8px] text-gray-300 mb-1">gCO₂eq/kWh</div>
        <div className="flex items-stretch gap-1">
          <div
            className="w-[6px] h-[60px] rounded-sm"
            style={{
              background:
                "linear-gradient(to bottom, #2ecc71, #8bc34a, #fdd835, #ff9800, #f4511e, #c62828)",
            }}
          />
          <div className="flex flex-col justify-between text-[8px] text-gray-300 h-[60px]">
            <span>0</span>
            <span>150</span>
            <span>300</span>
            <span>500</span>
            <span>800</span>
            <span>1200</span>
          </div>
        </div>
      </div>
    </div>
  );
}
