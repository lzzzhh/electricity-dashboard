import { useState, useRef, useEffect, useMemo } from "react";
import type { Metric } from "./types";
import { useFacilities, useLatest, useStats, useTimeseries, useSummary, useMarketLatest, useMarketTimeseries, useMarketRegions } from "./hooks/useApi";
import NavBar from "./components/NavBar";
import FilterPanel from "./components/FilterPanel";
import TopBar from "./components/TopBar";
import MapView from "./components/MapView";
import FloatingPanel from "./components/FloatingPanel";
import BottomPanel from "./components/BottomPanel";

export default function App() {
  const [activeTab, setActiveTab] = useState("map");
  const [filterOpen, setFilterOpen] = useState(false);
  const [metric, setMetric] = useState<Metric>("power_mw");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
  const [selectedFuels, setSelectedFuels] = useState<string[]>([]);

  const bottomRef = useRef<HTMLDivElement>(null);

  // Nav tab actions
  useEffect(() => {
    if (activeTab === "map") {
      setSelectedId(null);
      setFilterOpen(false);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else if (activeTab === "analytics") {
      setFilterOpen(true);
      bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
    const t = setTimeout(() => setActiveTab(""), 200);
    return () => clearTimeout(t);
  }, [activeTab]);

  const facilities = useFacilities();
  const latest = useLatest();
  const stats = useStats();
  const timeseries = useTimeseries(selectedId);
  const regionSummary = useSummary("region", metric);
  const fuelSummary = useSummary("fuel_tech", metric);
  const marketLatest = useMarketLatest();
  const marketRegions = useMarketRegions();
  const [marketFocus, setMarketFocus] = useState<string>("NSW1");
  const marketTimeseries = useMarketTimeseries(marketFocus);

  const selectedFacility = facilities.find(f => f.facility_id === selectedId) ?? null;
  const selectedReading = latest.find(d => d.facility_id === selectedId) ?? null;

  const allRegions = useMemo(() => [...new Set(facilities.map(f => f.network_region))].sort(), [facilities]);
  const allFuels = useMemo(() => [...new Set(facilities.map(f => f.fuel_tech))].sort(), [facilities]);

  // Auto-select all regions/fuels if none selected
  if (allRegions.length > 0 && selectedRegions.length === 0) {
    // use setTimeout to avoid setState during render
    setTimeout(() => setSelectedRegions([...allRegions]), 0);
  }
  if (allFuels.length > 0 && selectedFuels.length === 0) {
    setTimeout(() => setSelectedFuels([...allFuels]), 0);
  }

  const filteredFacilities = facilities.filter(
    f => selectedRegions.includes(f.network_region) && selectedFuels.includes(f.fuel_tech)
  );
  const filteredLatest = latest.filter(d => {
    const meta = facilities.find(f => f.facility_id === d.facility_id);
    return meta && selectedRegions.includes(meta.network_region) && selectedFuels.includes(meta.fuel_tech);
  });

  return (
    <div className="flex h-screen bg-[#eeebe5] overflow-hidden">
      {/* Left: Nav bar */}
      <NavBar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        filterOpen={filterOpen}
        onFilterToggle={() => setFilterOpen(!filterOpen)}
      />

      {/* Slide-out filter panel */}
      {filterOpen && (
        <FilterPanel
          metric={metric}
          onMetricChange={setMetric}
          regions={allRegions}
          selectedRegions={selectedRegions}
          onRegionsChange={setSelectedRegions}
          fuels={allFuels}
          selectedFuels={selectedFuels}
          onFuelsChange={setSelectedFuels}
        />
      )}

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar stats={stats} metric={metric} />

        {/* Map + floating panel */}
        <div className="flex-1 relative min-h-0">
          <MapView
            facilities={filteredFacilities}
            latest={filteredLatest}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />

          {/* Floating detail panel overlay */}
          {selectedFacility && selectedReading && (
            <FloatingPanel
              facility={selectedFacility}
              reading={selectedReading}
              timeseries={timeseries}
              summary={fuelSummary}
              onClose={() => setSelectedId(null)}
            />
          )}
        </div>

        {/* Bottom analytics */}
        <div ref={bottomRef}>
          <BottomPanel
            latest={filteredLatest}
            facilities={filteredFacilities}
            regionSummary={regionSummary}
            fuelSummary={fuelSummary}
            marketTimeseries={marketTimeseries}
            marketLatest={marketLatest}
            metric={metric}
          />
        </div>
      </div>
    </div>
  );
}
