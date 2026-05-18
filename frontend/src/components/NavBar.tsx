const icons = {
  map: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 6v16l7-4 8 4 7-4V2l-7 4-8-4-7 4Z" />
      <path d="M8 2v16M16 6v16" />
    </svg>
  ),
  filter: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
    </svg>
  ),
  chart: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  ),
};

interface Props {
  activeTab: string;
  onTabChange: (tab: string) => void;
  filterOpen: boolean;
  onFilterToggle: () => void;
}

export default function NavBar({ activeTab, onTabChange, filterOpen, onFilterToggle }: Props) {
  const tabs = [
    { id: "map", icon: icons.map, label: "Map" },
    { id: "analytics", icon: icons.chart, label: "Analytics" },
  ];

  return (
    <div className="w-14 flex-shrink-0 flex flex-col items-center py-3 gap-1 glass rounded-r-2xl">
      {/* Logo / brand */}
      <div className="w-8 h-8 rounded-lg bg-orange-500/10 flex items-center justify-center mb-2">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f97316" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
        </svg>
      </div>

      {/* Nav tabs */}
      {tabs.map(t => (
        <button
          key={t.id}
          onClick={() => onTabChange(t.id)}
          className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-150
            ${activeTab === t.id
              ? "bg-gray-100 text-gray-800"
              : "text-gray-400 hover:text-gray-600 hover:bg-gray-50"}`}
          title={t.label}
        >
          {t.icon}
        </button>
      ))}

      <div className="flex-1" />

      {/* Filter button */}
      <button
        onClick={onFilterToggle}
        className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-150
          ${filterOpen
            ? "bg-gray-100 text-gray-800"
            : "text-gray-400 hover:text-gray-600 hover:bg-gray-50"}`}
        title="Filters"
      >
        {icons.filter}
      </button>
    </div>
  );
}
