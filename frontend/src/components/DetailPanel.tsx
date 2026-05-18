import type { Facility, LatestReading, TimeseriesPoint, SummaryItem } from "../types";
import { FUEL_LABELS, FUEL_COLORS, carbonColor, ciLabel } from "../types";
import CIChart from "./CIChart";

interface Props {
  facility: Facility | null;
  reading: LatestReading | null;
  timeseries: TimeseriesPoint[];
  summary: SummaryItem[];
}

export default function DetailPanel({ facility, reading, timeseries, summary }: Props) {
  if (!facility || !reading) {
    return (
      <div className="flex-1 flex items-center justify-center px-2">
        <div className="text-center text-gray-400">
          <div className="text-sm mb-1">Select a facility</div>
          <div className="text-[11px] text-gray-300">Click a marker on the map<br />or choose from the zone list</div>
        </div>
      </div>
    );
  }

  const pwr = reading.power_mw;
  const em = reading.emissions_tco2e;
  const ci = (em * 1000) / Math.max(pwr, 1);
  const ciC = carbonColor(ci);
  const band = ciLabel(ci);
  const fuel = facility.fuel_tech;
  const fuelC = FUEL_COLORS[fuel] || "#888";
  const total = summary.reduce((s, i) => s + i.value, 0);

  return (
    <div className="flex-1 overflow-y-auto px-2 py-1.5">
      <div className="glass-card rounded-2xl p-3">
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-semibold text-gray-800">{facility.facility_name}</span>
        </div>
        <div className="text-[11px] text-gray-400 mb-2">
          {FUEL_LABELS[fuel] || fuel} · NEM {facility.network_region}
        </div>

        <div className="mb-1">
          <span className="text-3xl font-light" style={{ color: ciC }}>{ci.toFixed(0)}</span>
          <span className="text-xs text-gray-400 ml-1">gCO₂eq/kWh</span>
        </div>
        <div className="text-[9px] text-gray-400 uppercase tracking-wider mb-2">{band} carbon intensity</div>

        <div className="flex gap-2 mb-2">
          <div className="flex-1 text-center glass rounded-xl py-1.5">
            <div className="font-semibold text-orange-600">{pwr.toLocaleString()}</div>
            <div className="text-[9px] text-gray-400 uppercase">MW</div>
          </div>
          <div className="flex-1 text-center glass rounded-xl py-1.5">
            <div className="font-semibold text-red-500">{em.toLocaleString(undefined, { minimumFractionDigits: 1 })}</div>
            <div className="text-[9px] text-gray-400 uppercase">tCO₂e</div>
          </div>
        </div>
        <div className="text-[9px] text-gray-400 mb-3">{reading.timestamp?.slice(0, 19)}</div>

        {summary.length > 0 && total > 0 && (
          <>
            <div className="text-[9px] text-gray-400 uppercase tracking-wider mb-1">Electricity mix (NEM-wide)</div>
            {summary.map(s => {
              const fn = s.fuel || s.region || "";
              const pct = (s.value / total) * 100;
              const c = FUEL_COLORS[fn] || "#666";
              return (
                <div key={fn} className="flex items-center gap-1.5 py-0.5 text-[10px]">
                  <span className="w-[6px] h-[6px] rounded-full flex-shrink-0" style={{ background: c }} />
                  <span className="text-gray-500 w-[70px] truncate text-[10px]">{FUEL_LABELS[fn] || fn}</span>
                  <div className="flex-1 h-1 bg-white/60 rounded overflow-hidden">
                    <div className="h-full rounded" style={{ width: `${pct}%`, background: c }} />
                  </div>
                  <span className="text-gray-400 w-7 text-right text-[9px]">{pct.toFixed(1)}%</span>
                  <span className="text-gray-400 w-11 text-right text-[9px]">{s.value.toFixed(0)} MW</span>
                </div>
              );
            })}
          </>
        )}
      </div>

      {timeseries.length > 0 && (
        <div className="mt-2">
          <CIChart data={timeseries} color={ciC} name={facility.facility_name} />
        </div>
      )}
    </div>
  );
}
