import { useState } from "react";
import type { Metric } from "../types";
import { FUEL_LABELS } from "../types";

interface Props {
  metric: Metric;
  onMetricChange: (m: Metric) => void;
  regions: string[];
  selectedRegions: string[];
  onRegionsChange: (r: string[]) => void;
  fuels: string[];
  selectedFuels: string[];
  onFuelsChange: (f: string[]) => void;
}

export default function FilterPanel({
  metric, onMetricChange,
  regions, selectedRegions, onRegionsChange,
  fuels, selectedFuels, onFuelsChange,
}: Props) {
  const toggle = (arr: string[], item: string, setter: (v: string[]) => void) => {
    setter(arr.includes(item) ? arr.filter(x => x !== item) : [...arr, item]);
  };

  const allRegions = selectedRegions.length === regions.length;
  const allFuels = selectedFuels.length === fuels.length;

  return (
    <div className="w-[240px] flex-shrink-0 glass rounded-r-2xl flex flex-col overflow-hidden animate-in slide-in-from-left">
      <div className="px-3 py-2.5 border-b border-white/40">
        <span className="text-xs font-semibold text-gray-800">Filters</span>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">
        {/* Metric */}
        <div>
          <label className="text-[10px] uppercase tracking-wider text-gray-400 font-semibold mb-1 block">Metric</label>
          <div className="flex rounded-lg glass-input p-0.5">
            {(["power_mw", "emissions_tco2e"] as Metric[]).map(m => (
              <button
                key={m}
                onClick={() => onMetricChange(m)}
                className={`flex-1 text-[11px] py-1 rounded-md transition-all ${
                  metric === m ? "bg-white/80 text-gray-800 shadow-sm" : "text-gray-400 hover:text-gray-600"
                }`}
              >
                {m === "power_mw" ? "Power" : "CO₂"}
              </button>
            ))}
          </div>
        </div>

        {/* Regions */}
        <div>
          <label className="text-[10px] uppercase tracking-wider text-gray-400 font-semibold mb-1 block">Regions</label>
          <button
            onClick={() => onRegionsChange(allRegions ? [] : [...regions])}
            className="text-[10px] text-gray-400 hover:text-gray-600 mb-1"
          >
            {allRegions ? "Deselect all" : "Select all"}
          </button>
          <div className="flex flex-wrap gap-1">
            {regions.map(r => (
              <button
                key={r}
                onClick={() => toggle(selectedRegions, r, onRegionsChange)}
                className={`px-2 py-0.5 rounded-md text-[10px] transition-all ${
                  selectedRegions.includes(r)
                    ? "bg-gray-800/8 text-gray-800"
                    : "text-gray-400 hover:text-gray-600 hover:bg-gray-50"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        {/* Fuel tech */}
        <div>
          <label className="text-[10px] uppercase tracking-wider text-gray-400 font-semibold mb-1 block">Technology</label>
          <button
            onClick={() => onFuelsChange(allFuels ? [] : [...fuels])}
            className="text-[10px] text-gray-400 hover:text-gray-600 mb-1"
          >
            {allFuels ? "Deselect all" : "Select all"}
          </button>
          <div className="flex flex-wrap gap-1">
            {fuels.map(f => (
              <button
                key={f}
                onClick={() => toggle(selectedFuels, f, onFuelsChange)}
                className={`px-2 py-0.5 rounded-md text-[10px] transition-all ${
                  selectedFuels.includes(f)
                    ? "bg-gray-800/8 text-gray-800"
                    : "text-gray-400 hover:text-gray-600 hover:bg-gray-50"
                }`}
              >
                {FUEL_LABELS[f] || f}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
