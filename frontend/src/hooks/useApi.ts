import { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import type {
  Facility,
  LatestReading,
  Stats,
  SummaryItem,
  TimeseriesPoint,
  MarketReading,
  Metric,
} from "../types";

const API = "";

export function useFacilities() {
  const [data, setData] = useState<Facility[]>([]);
  const fetch = useCallback(async () => {
    try {
      const res = await axios.get<Facility[]>(`${API}/api/facilities`, { timeout: 3000 });
      setData(res.data);
    } catch { /* keep stale */ }
  }, []);
  useEffect(() => { fetch(); }, [fetch]);
  return data;
}

export function useLatest() {
  const [data, setData] = useState<LatestReading[]>([]);
  const fetch = useCallback(async () => {
    try {
      const res = await axios.get<LatestReading[]>(`${API}/api/facilities/latest`, { timeout: 3000 });
      setData(res.data);
    } catch { /* keep stale */ }
  }, []);
  useEffect(() => { fetch(); const t = setInterval(fetch, 4000); return () => clearInterval(t); }, [fetch]);
  return data;
}

export function useStats() {
  const [data, setData] = useState<Stats>({
    facilities_total: 0,
    measurements_total: 0,
    market_records: 0,
    last_measurement_ts: null,
    last_market_ts: null,
  });
  const fetch = useCallback(async () => {
    try {
      const res = await axios.get<Stats>(`${API}/api/stats`, { timeout: 3000 });
      setData(res.data);
    } catch { /* keep stale */ }
  }, []);
  useEffect(() => { fetch(); const t = setInterval(fetch, 4000); return () => clearInterval(t); }, [fetch]);
  return data;
}

export function useTimeseries(id: string | null) {
  const [data, setData] = useState<TimeseriesPoint[]>([]);
  useEffect(() => {
    if (!id) { setData([]); return; }
    let cancelled = false;
    const fetch = async () => {
      try {
        const res = await axios.get<TimeseriesPoint[]>(`${API}/api/facilities/${id}/timeseries`, { timeout: 5000 });
        if (!cancelled) setData(res.data);
      } catch { if (!cancelled) setData([]); }
    };
    fetch();
    const t = setInterval(fetch, 4000);
    return () => { cancelled = true; clearInterval(t); };
  }, [id]);
  return data;
}

export function useSummary(groupBy: "region" | "fuel_tech", metric: Metric) {
  const [data, setData] = useState<SummaryItem[]>([]);
  useEffect(() => {
    let cancelled = false;
    const fetch = async () => {
      try {
        const res = await axios.get<SummaryItem[]>(`${API}/api/summary`, {
          params: { group_by: groupBy, metric },
          timeout: 3000,
        });
        if (!cancelled) setData(res.data);
      } catch { if (!cancelled) setData([]); }
    };
    fetch();
    const t = setInterval(fetch, 4000);
    return () => { cancelled = true; clearInterval(t); };
  }, [groupBy, metric]);
  return data;
}

export function useMarketLatest() {
  const [data, setData] = useState<MarketReading[]>([]);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await axios.get<MarketReading[]>(`${API}/api/market/latest`, { timeout: 3000 });
        if (!cancelled) setData(res.data);
      } catch { if (!cancelled) setData([]); }
    })();
    return () => { cancelled = true; };
  }, []);
  return data;
}

export function useMarketTimeseries(region: string | null) {
  const [data, setData] = useState<MarketReading[]>([]);
  useEffect(() => {
    if (!region) { setData([]); return; }
    let cancelled = false;
    (async () => {
      try {
        const res = await axios.get<MarketReading[]>(`${API}/api/market/timeseries`, {
          params: { region },
          timeout: 10000,
        });
        if (!cancelled) setData(res.data);
      } catch { if (!cancelled) setData([]); }
    })();
    return () => { cancelled = true; };
  }, [region]);
  return data;
}

export function useMarketRegions() {
  const [data, setData] = useState<string[]>([]);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await axios.get<string[]>(`${API}/api/market/regions`, { timeout: 3000 });
        if (!cancelled) setData(res.data);
      } catch { if (!cancelled) setData([]); }
    })();
    return () => { cancelled = true; };
  }, []);
  return data;
}
