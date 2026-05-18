import { useState } from "react";
import type { Facility, LatestReading, Metric } from "../types";
import { FUEL_LABELS, carbonColor } from "../types";

interface Props {
  facilities: Facility[];
  latest: LatestReading[];
  regions: string[];
  fuels: string[];
  metric: Metric;
  stats: { messages_total: number; facilities_online: number; last_update: string };
  selectedId: string | null;
  onSelect: (id: string) => void;
  onMetricChange: (m: Metric) => void;
  selectedRegions: string[];
  onRegionsChange: (r: string[]) => void;
  selectedFuels: string[];
  onFuelsChange: (f: string[]) => void;
}

export default function Sidebar({
  facilities, latest, regions, fuels, metric, stats,
  selectedId, onSelect, onMetricChange,
  selectedRegions, onRegionsChange, selectedFuels, onFuelsChange,
}: Props) {
  const latestMap = new Map(latest.map(d => [d.facility_id, d]));
  const allRegions = [...new Set(facilities.map(f => f.network_region))].sort();
  const allFuels = [...new Set(facilities.map(f => f.fuel_tech))].sort();

  const filtered = facilities.filter(
    f => selectedRegions.includes(f.network_region) && selectedFuels.includes(f.fuel_tech)
  );

  return (
    <div className="w-[250px] glass rounded-r-2xl flex flex-col h-full overflow-hidden">
      <div className="p-2 border-b border-white/40">
        <div className="flex items-center gap-1.5 mb-3">
          <span className="text-orange-500 text-sm">&#9889;</span>
          <span className="font-semibold text-gray-800 text-sm">NEM Monitor</span>
        </div>

        <label className="text-[10px] uppercase tracking-wider text-gray-400 font-semibold mb-0.5 block">Metric</label>
        <select
          value={metric}
          onChange={e => onMetricChange(e.target.value as Metric)}
          className="w-full glass-input rounded-lg text-xs py-1 px-2 mb-2.5 text-gray-700"
        >
          <option value="power_mw">Power (MW)</option>
          <option value="emissions_tco2e">Carbon intensity</option>
        </select>

        <MultiSelect
          label="Regions"
          options={allRegions}
          selected={selectedRegions}
          onChange={onRegionsChange}
        />
        <MultiSelect
          label="Technology"
          options={allFuels}
          selected={selectedFuels}
          onChange={onFuelsChange}
          formatLabel={FUEL_LABELS}
        />

        <div className="flex gap-3 text-[10px] text-gray-400 mt-2">
          <span><b className="text-gray-600">{stats.messages_total.toLocaleString()}</b> messages</span>
          <span><b className="text-green-600">● {stats.facilities_online}</b> online</span>
        </div>
        {stats.last_update && (
          <div className="text-[10px] text-gray-400 mt-0.5">
            Updated {stats.last_update.slice(0, 19).replace("T", " ")}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="text-[10px] uppercase tracking-wider text-gray-400 font-semibold px-2 pt-2 pb-1">
          Facilities
        </div>
        {filtered.map(f => {
          const d = latestMap.get(f.facility_id);
          const pwr = d?.power_mw ?? 0;
          const em = d?.emissions_tco2e ?? 0;
          const ci = (em * 1000) / Math.max(pwr, 1);
          const dot = carbonColor(ci);
          const isSelected = selectedId === f.facility_id;
          return (
            <button
              key={f.facility_id}
              onClick={() => onSelect(f.facility_id)}
              className={`w-full text-left px-2 py-1 text-[11px] flex items-center gap-1.5
                transition-colors rounded-lg mx-1
                ${isSelected ? "bg-white/60 text-gray-900 font-semibold" : "text-gray-500 glass-hover"}`}
            >
              <span className="w-[6px] h-[6px] rounded-full flex-shrink-0" style={{ background: dot }} />
              <span className="truncate">{f.facility_name}</span>
              <span className="ml-auto text-[10px] text-gray-400 flex-shrink-0">{pwr.toFixed(0)} MW</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function MultiSelect({
  label, options, selected, onChange, formatLabel,
}: {
  label: string;
  options: string[];
  selected: string[];
  onChange: (v: string[]) => void;
  formatLabel?: Record<string, string>;
}) {
  const [open, setOpen] = useState(false);
  const all = selected.length === options.length;
  return (
    <div className="mb-2 relative">
      <label className="text-[10px] uppercase tracking-wider text-gray-400 font-semibold mb-0.5 block">{label}</label>
      <button
        onClick={() => setOpen(!open)}
        className="w-full glass-input rounded-lg text-xs py-1 px-2 text-left flex items-center justify-between text-gray-600"
      >
        <span className="truncate">{all ? "All" : selected.map(s => formatLabel?.[s] ?? s).join(", ") || "None"}</span>
        <span className="text-gray-400 ml-1">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="absolute z-50 glass-card rounded-xl shadow-lg mt-0.5 w-full max-h-40 overflow-y-auto">
          <button
            className="w-full text-left px-2 py-1 text-[11px] text-gray-500 glass-hover border-b border-white/40"
            onClick={() => { onChange(selected.length === options.length ? [] : [...options]); setOpen(false); }}
          >
            {all ? "Deselect all" : "Select all"}
          </button>
          {options.map(o => (
            <label key={o} className="flex items-center gap-1.5 px-2 py-1 text-[11px] text-gray-600 glass-hover cursor-pointer">
              <input
                type="checkbox"
                checked={selected.includes(o)}
                onChange={() => {
                  onChange(selected.includes(o) ? selected.filter(s => s !== o) : [...selected, o]);
                }}
                className="w-3 h-3"
              />
              {formatLabel?.[o] ?? o}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
