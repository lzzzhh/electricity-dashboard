import React, { useMemo, useState } from "react";
import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";
import type { LatestReading, Facility, SummaryItem, Metric, MarketReading } from "../types";
import { FUEL_LABELS, FUEL_COLORS, REGION_COLORS } from "../types";

interface Props {
  latest: LatestReading[];
  facilities: Facility[];
  regionSummary: SummaryItem[];
  fuelSummary: SummaryItem[];
  marketTimeseries: MarketReading[];
  marketLatest: MarketReading[];
  metric: Metric;
}

type TabKey = "region" | "fuel" | "prices" | "demand" | "table";

export default function BottomPanel({ latest, facilities, regionSummary, fuelSummary, marketTimeseries, marketLatest, metric }: Props) {
  const isPower = metric === "power_mw";
  const facMap = useMemo(() => new Map(facilities.map(f => [f.facility_id, f])), [facilities]);

  const rows = useMemo(
    () =>
      latest.slice(0, 20).map(d => {
        const meta = facMap.get(d.facility_id);
        const ci = (d.emissions_tco2e * 1000) / Math.max(d.power_mw, 1);
        return {
          "Facility": meta?.facility_name || d.facility_id,
          "Region": meta?.network_region || "",
          "Technology": FUEL_LABELS[meta?.fuel_tech || ""] || meta?.fuel_tech || "",
          "Power (MW)": d.power_mw.toLocaleString(),
          "CO\u2082 (t)": d.emissions_tco2e.toFixed(1),
          "CI (g/kWh)": ci.toFixed(0),
        };
      }),
    [latest, facMap]
  );

  // Market timeseries grouped by region
  const marketByRegion = useMemo(() => {
    const map = new Map<string, MarketReading[]>();
    for (const r of marketTimeseries) {
      const arr = map.get(r.region) || [];
      arr.push(r);
      map.set(r.region, arr);
    }
    return map;
  }, [marketTimeseries]);

  const [tab, setTab] = useState<TabKey>("region");
  const [focusRegion, setFocusRegion] = useState("NSW1");

  const tabs: { key: TabKey; label: string }[] = [
    { key: "region", label: `By Region (${isPower ? "MW" : "tCO₂e"})` },
    { key: "fuel", label: `By Technology (${isPower ? "MW" : "tCO₂e"})` },
    { key: "prices", label: "Market Prices" },
    { key: "demand", label: "Demand" },
    { key: "table", label: "Latest Data" },
  ];

  // Prepare price chart data
  const priceChartData = useMemo(() => {
    const allRegions = [...new Set(marketTimeseries.map(r => r.region))].sort();
    // Build time-aligned data
    const timeMap = new Map<string, Record<string, number>>();
    for (const r of marketTimeseries) {
      if (!timeMap.has(r.timestamp)) timeMap.set(r.timestamp, {});
      timeMap.get(r.timestamp)![r.region] = r.price_aud_mwh;
    }
    return Array.from(timeMap.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([ts, vals]) => ({ ts: new Date(ts).toLocaleString([], { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }), ...vals }));
  }, [marketTimeseries]);

  return (
    <div className="glass rounded-t-2xl">
      <div className="flex items-center gap-2 px-3 py-1 text-[10px] text-gray-400">
        <span>{new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })} · Historical</span>
        <span className="text-gray-300">|</span>
        <span>Auto-refresh 4s</span>
        <span className="text-gray-300">|</span>
        <span>{facilities.length} dispatch units</span>
        <span className="ml-auto text-gray-300">Data: NEM 5-min dispatch · May 1-7, 2026</span>
      </div>
      <div className="flex border-b border-white/40 px-3">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-2.5 py-1.5 text-[11px] border-b-2 transition-colors ${
              tab === t.key ? "border-orange-500 text-gray-800" : "border-transparent text-gray-400 hover:text-gray-600"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="h-[220px] p-2">
        {tab === "region" && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={regionSummary.filter(s => s.group).map(s => ({ name: s.group, value: s.value }))} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8e5e0" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#888" }} />
              <YAxis tick={{ fontSize: 10, fill: "#888" }} unit={isPower ? " MW" : " t"} />
              <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} formatter={(v: number) => [isPower ? `${v.toFixed(1)} MW` : `${v.toFixed(1)} tCO₂e`]} />
              <Bar dataKey="value" name={isPower ? "Power (MW)" : "Emissions (tCO₂e)"} radius={[3, 3, 0, 0]}>
                {regionSummary.filter(s => s.group).map((s, i) => (
                  <Cell key={i} fill={REGION_COLORS[s.group] || "#e65100"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
        {tab === "fuel" && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={fuelSummary.filter(s => s.group).map(s => ({ name: FUEL_LABELS[s.group] || s.group, value: s.value, fuel: s.group }))} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8e5e0" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#888" }} />
              <YAxis tick={{ fontSize: 10, fill: "#888" }} unit={isPower ? " MW" : " t"} />
              <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} formatter={(v: number) => [isPower ? `${v.toFixed(1)} MW` : `${v.toFixed(1)} tCO₂e`]} />
              <Bar dataKey="value" name={isPower ? "Power (MW)" : "Emissions (tCO₂e)"} radius={[3, 3, 0, 0]}>
                {fuelSummary.filter(s => s.group).map((s, i) => (
                  <Cell key={i} fill={FUEL_COLORS[s.group] || "#666"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
        {tab === "prices" && (
          <div className="flex gap-2 h-full">
            <div className="flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={priceChartData} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e8e5e0" />
                  <XAxis dataKey="ts" tick={{ fontSize: 9, fill: "#888" }} />
                  <YAxis tick={{ fontSize: 9, fill: "#888" }} />
                  <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                  {[...new Set(marketTimeseries.map(r => r.region))].sort().map(region => (
                    <Line key={region} type="monotone" dataKey={region} stroke={REGION_COLORS[region] || "#888"} strokeWidth={1} dot={false} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="w-[140px] flex flex-col gap-1 overflow-auto">
              {marketLatest.sort((a, b) => b.price_aud_mwh - a.price_aud_mwh).map(r => (
                <div key={r.region} className="flex items-center gap-1 text-[10px]">
                  <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: REGION_COLORS[r.region] || "#888" }} />
                  <span className="text-gray-700 font-medium">{r.region}</span>
                  <span className="ml-auto text-gray-500">${r.price_aud_mwh.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {tab === "demand" && (
          <div className="flex gap-2 h-full">
            <div className="flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={(marketByRegion.get(focusRegion) || []).map(r => ({
                  ts: new Date(r.timestamp).toLocaleString([], { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }),
                  demand: r.demand_mw,
                }))} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e8e5e0" />
                  <XAxis dataKey="ts" tick={{ fontSize: 9, fill: "#888" }} />
                  <YAxis tick={{ fontSize: 9, fill: "#888" }} />
                  <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                  <Line type="monotone" dataKey="demand" stroke="#e65100" strokeWidth={1.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="w-[120px] flex flex-col gap-1">
              <div className="text-[10px] text-gray-400 mb-1">Focus region</div>
              {[...new Set(marketTimeseries.map(r => r.region))].sort().map(region => (
                <button
                  key={region}
                  onClick={() => setFocusRegion(region)}
                  className={`text-[10px] px-1.5 py-0.5 rounded text-left ${
                    focusRegion === region ? "bg-orange-100 text-orange-700 font-medium" : "text-gray-500 hover:bg-gray-100"
                  }`}
                >
                  {region}
                </button>
              ))}
            </div>
          </div>
        )}
        {tab === "table" && (
          <div className="overflow-auto h-full text-[10px]">
            <table className="w-full border-collapse">
              <thead>
                <tr className="text-gray-400 text-left">
                  <th className="py-1 px-1.5 font-medium">Facility</th>
                  <th className="py-1 px-1.5 font-medium">Region</th>
                  <th className="py-1 px-1.5 font-medium">Tech</th>
                  <th className="py-1 px-1.5 font-medium text-right">MW</th>
                  <th className="py-1 px-1.5 font-medium text-right">tCO₂</th>
                  <th className="py-1 px-1.5 font-medium text-right">g/kWh</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className={i % 2 === 0 ? "bg-white/30" : ""}>
                    <td className="py-0.5 px-1.5 text-gray-800">{r["Facility"]}</td>
                    <td className="py-0.5 px-1.5 text-gray-500">{r["Region"]}</td>
                    <td className="py-0.5 px-1.5 text-gray-500">{r["Technology"]}</td>
                    <td className="py-0.5 px-1.5 text-right text-gray-600">{r["Power (MW)"]}</td>
                    <td className="py-0.5 px-1.5 text-right text-gray-600">{r["CO\u2082 (t)"]}</td>
                    <td className="py-0.5 px-1.5 text-right text-gray-600">{r["CI (g/kWh)"]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
