'use client'

import { motion } from 'framer-motion'

interface FaultCardProps {
  fault: string
  severity: number
  index: number
}

function formatFaultName(fault: string): string {
  return fault
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function getSeverityColorClass(severity: number): string {
  if (severity < 0.4) return 'severity-low'
  if (severity <= 0.7) return 'severity-mid'
  return 'severity-high'
}

function getSeverityBgClass(severity: number): string {
  if (severity < 0.4) return 'bg-green-500'
  if (severity <= 0.7) return 'bg-amber-500'
  return 'bg-red-500'
}

function getSeverityLabel(severity: number): string {
  if (severity < 0.4) return 'Minor'
  if (severity <= 0.7) return 'Moderate'
  return 'Severe'
}

export default function FaultCard({ fault, severity, index }: FaultCardProps) {
  const pct = Math.round(severity * 100)
  const colorClass = getSeverityColorClass(severity)
  const bgClass = getSeverityBgClass(severity)
  const label = getSeverityLabel(severity)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1, ease: [0.22, 1, 0.36, 1] }}
      className="rounded-xl border border-white/10 bg-[#111111] p-5 hover:border-white/20 transition-colors"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-white tracking-tight">{formatFaultName(fault)}</h3>
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded-full border ${
            severity < 0.4
              ? 'text-green-400 border-green-400/30 bg-green-400/10'
              : severity <= 0.7
              ? 'text-amber-400 border-amber-400/30 bg-amber-400/10'
              : 'text-red-400 border-red-400/30 bg-red-400/10'
          }`}
        >
          {label}
        </span>
      </div>

      {/* Severity bar track */}
      <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
        <motion.div
          data-testid="severity-bar"
          className={`h-full rounded-full ${bgClass} ${colorClass}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, delay: index * 0.1 + 0.2, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>

      {/* Percentage */}
      <div className="mt-2 flex justify-end">
        <span className="text-xs text-gray-400 tabular-nums">{pct}%</span>
      </div>
    </motion.div>
  )
}
