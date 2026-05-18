export interface Facility {
  facility_id: string;
  facility_name: string;
  network_region: string;
  fuel_tech: string;
  latitude: number;
  longitude: number;
  station_type?: string;
}

export interface LatestReading {
  facility_id: string;
  power_mw: number;
  emissions_tco2e: number;
  timestamp: string;
}

export interface Stats {
  facilities_total: number;
  measurements_total: number;
  market_records: number;
  last_measurement_ts: string | null;
  last_market_ts: string | null;
}

export interface SummaryItem {
  group: string;
  value: number;
}

export interface MarketReading {
  region: string;
  timestamp: string;
  price_aud_mwh: number;
  demand_mw: number;
}

export type Metric = "power_mw" | "emissions_tco2e";

export const FUEL_COLORS: Record<string, string> = {
  coal_black: "#5c3a24",
  coal_brown: "#7d5240",
  gas_ccgt:   "#e65100",
  gas_ocgt:   "#ff8f00",
  gas_wcmg:   "#e65100",
  gas_steam:  "#bf360c",
  gas_recip:  "#ff8f00",
  hydro:      "#29b6f6",
  battery:    "#66bb6a",
  battery_charging:    "#43a047",
  battery_discharging: "#81c784",
  wind:       "#81c784",
  solar:      "#ffd600",
  solar_utility: "#fdd835",
  bioenergy:  "#8d6e63",
  bioenergy_biogas: "#8d6e63",
  distillate: "#ff8f00",
  load:       "#78909c",
};

export const FUEL_LABELS: Record<string, string> = {
  coal_black: "Coal (black)",
  coal_brown: "Coal (brown)",
  gas_ccgt:   "Gas (CCGT)",
  gas_ocgt:   "Gas (OCGT)",
  gas_wcmg:   "Gas (WCMG)",
  gas_steam:  "Gas (Steam)",
  gas_recip:  "Gas (Recip)",
  hydro:      "Hydro",
  battery:    "Battery storage",
  battery_charging:    "Battery (charging)",
  battery_discharging: "Battery (discharging)",
  wind:       "Wind",
  solar:      "Solar",
  solar_utility: "Solar (utility)",
  bioenergy:  "Biomass",
  bioenergy_biogas: "Biogas",
  distillate: "Distillate",
  load:       "Dispatchable Load",
};

export const REGION_COLORS: Record<string, string> = {
  NSW:  "#e65100",
  NSW1: "#e65100",
  QLD:  "#8e24aa",
  QLD1: "#8e24aa",
  VIC:  "#1565c0",
  VIC1: "#1565c0",
  SA:   "#fdd835",
  SA1:  "#fdd835",
  TAS:  "#2e7d32",
  TAS1: "#2e7d32",
};

export const CARBON_SCALE: [number, string][] = [
  [50,   "#2ecc71"],
  [150,  "#8bc34a"],
  [300,  "#fdd835"],
  [500,  "#ff9800"],
  [800,  "#f4511e"],
  [1200, "#c62828"],
];

export const CI_LABELS: [number, string][] = [
  [50,   "very low"],
  [150,  "low"],
  [300,  "medium"],
  [500,  "high"],
  [800,  "very high"],
  [1200, "extreme"],
];

export function carbonColor(val: number): string {
  if (val <= 0) return "#2ecc71";
  for (const [t, c] of CARBON_SCALE) {
    if (val < t) return c;
  }
  return CARBON_SCALE[CARBON_SCALE.length - 1][1];
}

export function ciLabel(val: number): string {
  for (const [t, lbl] of CI_LABELS) {
    if (val < t) return lbl;
  }
  return CI_LABELS[CI_LABELS.length - 1][1];
}

export interface TimeseriesPoint {
  timestamp: string;
  power_mw: number;
  emissions_tco2e: number;
}
