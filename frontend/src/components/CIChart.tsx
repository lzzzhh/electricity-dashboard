import { useMemo } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { TimeseriesPoint } from "../types";

interface Props {
  data: TimeseriesPoint[];
  color: string;
  name: string;
}

export default function CIChart({ data, color, name }: Props) {
  const chartData = useMemo(() =>
    data.map(d => ({
      t: new Date(d.timestamp).toLocaleString([], { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" }),
      ci: (d.emissions_tco2e * 1000) / Math.max(d.power_mw, 1),
    })),
    [data]
  );

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-2">
      <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">{name} — Carbon intensity trend</div>
      <ResponsiveContainer width="100%" height={120}>
        <LineChart data={chartData} margin={{ top: 2, right: 2, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="t" tick={{ fontSize: 9, fill: "#aaa" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 9, fill: "#aaa" }} axisLine={false} tickLine={false} width={30} />
          <Tooltip
            contentStyle={{ fontSize: 11, borderRadius: 4, border: "1px solid #e4e4ea" }}
            formatter={(v) => [`${Number(v).toFixed(0)} gCO₂/kWh`]}
          />
          <Line type="monotone" dataKey="ci" stroke={color} strokeWidth={1.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
