import { useState } from 'react'
import { useGraphStore } from '../store/graph'

const EDGE_TYPES = [
  { type: 'CITES', label: 'Cites', style: 'solid' },
  { type: 'SIMILAR_TO', label: 'Similar', style: 'dashed' },
  { type: 'MENTIONS', label: 'Mentions', style: 'dotted' },
  { type: 'RELATED_TO', label: 'Related', style: 'dotted' },
]

const EDGE_COLORS: Record<string, string> = {
  CITES: '#94a3b8',
  SIMILAR_TO: '#22d3ee',
  MENTIONS: '#f59e0b',
  RELATED_TO: '#a78bfa',
}

function EdgeStyleLine({ style, color }: { style: string; color: string }) {
  const dashArray =
    style === 'dashed' ? '4 3' : style === 'dotted' ? '1.5 2' : undefined
  return (
    <svg width="24" height="10" className="shrink-0">
      <line
        x1="0"
        y1="5"
        x2="24"
        y2="5"
        stroke={color}
        strokeWidth="1.5"
        strokeDasharray={dashArray}
      />
    </svg>
  )
}

export default function FilterPanel() {
  const [collapsed, setCollapsed] = useState(true)
  const { visibleEdgeTypes, yearRange, toggleEdgeType, setYearRange, toggleGraph, showGraph } =
    useGraphStore()

  return (
    <div className="absolute bottom-4 left-4 z-10">
      <div className="bg-surface border border-border rounded-card overflow-hidden">
        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="flex items-center gap-2 px-3 py-2 w-full text-left
                     text-xs text-textMuted hover:text-textPrimary transition-colors"
        >
          <span>{collapsed ? '▲' : '▼'}</span>
          <span>Filters</span>
        </button>

        {!collapsed && (
          <div className="px-3 pb-3 space-y-3 border-t border-border pt-3">
            {/* Edge type toggles */}
            <div>
              <p className="text-xs text-textMuted uppercase tracking-wider mb-2">Edge Types</p>
              <div className="space-y-1.5">
                {EDGE_TYPES.map(({ type, label, style }) => {
                  const active = visibleEdgeTypes.has(type)
                  return (
                    <button
                      key={type}
                      onClick={() => toggleEdgeType(type)}
                      className={`flex items-center gap-2 w-full text-left rounded px-2 py-1
                                  transition-colors text-xs
                                  ${active ? 'text-textPrimary' : 'text-textMuted opacity-50'}`}
                    >
                      <EdgeStyleLine style={style} color={EDGE_COLORS[type]} />
                      <span>{label}</span>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Year range */}
            <div>
              <p className="text-xs text-textMuted uppercase tracking-wider mb-2">
                Year: {yearRange[0]} – {yearRange[1]}
              </p>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="1990"
                  max={String(new Date().getFullYear())}
                  value={String(yearRange[0] ?? 1990)}
                  onChange={(e) => setYearRange([+e.target.value, yearRange[1]])}
                  className="w-full accent-primary"
                />
                <input
                  type="range"
                  min="1990"
                  max={String(new Date().getFullYear())}
                  value={String(yearRange[1] ?? new Date().getFullYear())}
                  onChange={(e) => setYearRange([yearRange[0], +e.target.value])}
                  className="w-full accent-primary"
                />
              </div>
            </div>

            {/* Toggle graph visibility */}
            <button
              onClick={toggleGraph}
              className="w-full text-xs rounded-card px-2 py-1.5 border border-border
                         text-textMuted hover:text-textPrimary transition-colors"
            >
              {showGraph ? 'Hide Graph' : 'Show Graph'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
