import type { Stats, Metric } from "../types";

interface Props {
  stats: Stats;
  metric: Metric;
}

export default function TopBar({ stats, metric }: Props) {
  const ts = stats.last_measurement_ts ? stats.last_measurement_ts.slice(0, 19).replace("T", " ") : "";
  const metricLabel = metric === "power_mw" ? "Power (MW)" : "Carbon intensity";

  return (
    <div className="flex items-center gap-3 px-3 py-1.5 glass rounded-none text-xs flex-wrap">
      <span className="font-semibold text-gray-800 text-sm">NEM Electricity Monitor</span>
      <span className="chip"><span className="dot bg-green-600" /> CSV data loaded</span>
      <span className="chip">NEM · Australia</span>
      <span className="chip">Metric: {metricLabel}</span>
      <span className="ml-auto text-gray-400 text-[11px]">
        {stats.facilities_total} units · {stats.measurements_total.toLocaleString()} records · {stats.market_records.toLocaleString()} market · {ts}
      </span>
    </div>
  );
}
