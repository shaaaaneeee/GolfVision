'use client'

import { motion } from 'framer-motion'

interface CoachingPanelProps {
  coaching: string
}

function GolfClubIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 2L8 22" />
      <path d="M8 16l8 2" />
      <ellipse cx="14" cy="19" rx="3" ry="1.5" />
    </svg>
  )
}

export default function CoachingPanel({ coaching }: CoachingPanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="rounded-xl border border-accent/20 bg-accent/5 p-6"
    >
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10 ring-1 ring-accent/20 text-accent">
          <GolfClubIcon />
        </div>
        <h3 className="text-sm font-semibold uppercase tracking-widest text-accent">
          Coach Feedback
        </h3>
      </div>

      {/* Body */}
      <p className="text-gray-300 leading-relaxed text-[0.9375rem]">{coaching}</p>
    </motion.div>
  )
}
