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
  A1StateYear,
  A1RenewableProject,
  A1Summary,
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

// ── Assignment 1 hooks ──

export function useA1Summary() {
  const [data, setData] = useState<A1Summary | null>(null);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await axios.get<A1Summary>(`${API}/api/assignment1/summary`, { timeout: 3000 });
        if (!cancelled) setData(res.data);
      } catch { if (!cancelled) setData(null); }
    })();
    return () => { cancelled = true; };
  }, []);
  return data;
}

export function useA1StateYear() {
  const [data, setData] = useState<A1StateYear[]>([]);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await axios.get<A1StateYear[]>(`${API}/api/assignment1/state_year`, { timeout: 3000 });
        if (!cancelled) setData(res.data);
      } catch { if (!cancelled) setData([]); }
    })();
    return () => { cancelled = true; };
  }, []);
  return data;
}

export function useA1Renewable(geocodedOnly = true) {
  const [data, setData] = useState<A1RenewableProject[]>([]);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await axios.get<A1RenewableProject[]>(`${API}/api/assignment1/renewable_projects`, {
          params: { geocoded_only: geocodedOnly },
          timeout: 3000,
        });
        if (!cancelled) setData(res.data);
      } catch { if (!cancelled) setData([]); }
    })();
    return () => { cancelled = true; };
  }, [geocodedOnly]);
  return data;
}
