import { useState, useMemo } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { Facility, LatestReading, TimeseriesPoint, SummaryItem } from "../types";
import { FUEL_LABELS, FUEL_COLORS, carbonColor, ciLabel } from "../types";

interface Props {
  facility: Facility;
  reading: LatestReading;
  timeseries: TimeseriesPoint[];
  summary: SummaryItem[];
  onClose: () => void;
}

type Tab = "overview" | "chart" | "mix";

export default function FloatingPanel({ facility, reading, timeseries, summary, onClose }: Props) {
  const [tab, setTab] = useState<Tab>("overview");

  const pwr = reading.power_mw;
  const em = reading.emissions_tco2e;
  const ci = (em * 1000) / Math.max(pwr, 1);
  const ciC = carbonColor(ci);
  const band = ciLabel(ci);
  const fuel = facility.fuel_tech;
  const total = summary.reduce((s, i) => s + i.value, 0);

  // Timeseries chart data
  const chartData = useMemo(() =>
    timeseries.map(d => ({
      t: new Date(d.timestamp).toLocaleString([], { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }),
      ci: (d.emissions_tco2e * 1000) / Math.max(d.power_mw, 1),
      power: d.power_mw,
    })),
    [timeseries]
  );

  return (
    <div className="absolute top-3 right-3 bottom-3 w-[380px] z-[900] glass-card rounded-2xl shadow-lg flex flex-col overflow-hidden pointer-events-auto">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2.5 border-b border-white/40">
        <button
          onClick={onClose}
          className="w-6 h-6 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <span className="text-sm font-semibold text-gray-800 truncate flex-1">{facility.facility_name}</span>
        <button className="w-6 h-6 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-600">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
        </button>
      </div>

      {/* Fuel + region subtitle */}
      <div className="px-3 pt-1.5">
        <span className="text-[11px] text-gray-400">
          {FUEL_LABELS[fuel] || fuel} · NEM {facility.network_region}
        </span>
      </div>

      {/* Segmented control */}
      <div className="px-3 py-2">
        <div className="flex rounded-lg glass-input p-0.5">
          {(["overview", "chart", "mix"] as Tab[]).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex-1 text-[11px] py-1 rounded-md transition-all ${
                tab === t ? "bg-white/80 text-gray-800 shadow-sm" : "text-gray-400 hover:text-gray-600"
              }`}
            >
              {t === "overview" ? "Overview" : t === "chart" ? "Chart" : "Mix"}
            </button>
          ))}
        </div>
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-y-auto px-3">
        {tab === "overview" && (
          <div className="space-y-2 pb-2">
            {/* CI big number */}
            <div className="glass rounded-xl p-3 text-center">
              <div className="text-4xl font-light tracking-tight" style={{ color: ciC }}>
                {ci.toFixed(0)}
              </div>
              <div className="text-[11px] text-gray-400">gCO₂eq/kWh</div>
              <div className="text-[9px] text-gray-400 uppercase tracking-wider mt-0.5">{band} carbon intensity</div>
            </div>

            {/* Power & Emissions cards */}
            <div className="flex gap-2">
              <div className="flex-1 glass rounded-xl p-2.5 text-center">
                <div className="font-semibold text-orange-600 text-lg">{pwr.toLocaleString()}</div>
                <div className="text-[9px] text-gray-400 uppercase">MW</div>
              </div>
              <div className="flex-1 glass rounded-xl p-2.5 text-center">
                <div className="font-semibold text-red-500 text-lg">{em.toLocaleString(undefined, { minimumFractionDigits: 1 })}</div>
                <div className="text-[9px] text-gray-400 uppercase">tCO₂e</div>
              </div>
            </div>

            {/* Timestamp */}
            <div className="text-[9px] text-gray-400">{reading.timestamp?.slice(0, 19)}</div>
          </div>
        )}

        {tab === "chart" && chartData.length > 0 && (
          <div className="pb-2 space-y-2">
            {/* CI Chart */}
            <div className="bg-white border border-gray-200 rounded-lg p-2">
              <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">Carbon intensity (gCO₂/kWh)</div>
              <ResponsiveContainer width="100%" height={110}>
                <LineChart data={chartData} margin={{ top: 2, right: 2, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="t" tick={{ fontSize: 9, fill: "#aaa" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 9, fill: "#aaa" }} axisLine={false} tickLine={false} width={30} />
                  <Tooltip contentStyle={{ fontSize: 11, borderRadius: 4, border: "1px solid #e4e4ea" }} />
                  <Line type="monotone" dataKey="ci" stroke={ciC} strokeWidth={1.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            {/* Power Chart */}
            <div className="bg-white border border-gray-200 rounded-lg p-2">
              <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">Power output (MW)</div>
              <ResponsiveContainer width="100%" height={110}>
                <LineChart data={chartData} margin={{ top: 2, right: 2, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="t" tick={{ fontSize: 9, fill: "#aaa" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 9, fill: "#aaa" }} axisLine={false} tickLine={false} width={30} />
                  <Tooltip contentStyle={{ fontSize: 11, borderRadius: 4, border: "1px solid #e4e4ea" }} />
                  <Line type="monotone" dataKey="power" stroke="#e65100" strokeWidth={1.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {tab === "chart" && chartData.length === 0 && (
          <div className="flex items-center justify-center h-40 text-gray-400 text-xs">
            No timeseries data available
          </div>
        )}

        {tab === "mix" && (
          <div className="pb-2 space-y-1.5">
            {summary.length > 0 && total > 0 ? (
              summary.filter(s => s.value > 0).map(s => {
                const fn = s.group;
                const pct = (s.value / total) * 100;
                const c = FUEL_COLORS[fn] || "#666";
                return (
                  <div key={fn || "unknown"} className="glass rounded-lg p-2">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-1.5">
                        <span className="w-[6px] h-[6px] rounded-full flex-shrink-0" style={{ background: c }} />
                        <span className="text-[11px] text-gray-700">{FUEL_LABELS[fn] || fn}</span>
                      </div>
                      <span className="text-[10px] text-gray-400">{pct.toFixed(1)}%</span>
                    </div>
                    <div className="h-1.5 bg-white/60 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: c }} />
                    </div>
                    <div className="text-[9px] text-gray-400 mt-0.5">{s.value.toFixed(0)} MW</div>
                  </div>
                );
              })
            ) : (
              <div className="flex items-center justify-center h-40 text-gray-400 text-xs">
                No mix data available
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom timeline bar */}
      <div className="border-t border-white/40 px-3 py-2">
        <div className="flex items-center gap-2">
          <button className="w-5 h-5 rounded flex items-center justify-center text-gray-400 hover:text-gray-600">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="19,20 9,12 19,4" /></svg>
          </button>
          <div className="flex-1 h-1 bg-gray-200 rounded-full relative">
            <div className="absolute inset-y-0 left-0 w-2/3 bg-gray-400 rounded-full" />
            <div className="absolute top-1/2 -translate-y-1/2 left-2/3 w-3 h-3 bg-white border-2 border-gray-400 rounded-full" />
          </div>
          <button className="w-5 h-5 rounded flex items-center justify-center text-gray-400 hover:text-gray-600">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,4 15,12 5,20" /></svg>
          </button>
        </div>
      </div>
    </div>
  );
}
