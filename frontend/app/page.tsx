'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import VideoUpload from '@/components/VideoUpload'
import VideoRecorder from '@/components/VideoRecorder'

type Tab = 'record' | 'upload'

const TABS: { value: Tab; label: string; icon: React.ReactNode }[] = [
  {
    value: 'record',
    label: 'Record',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <circle cx="12" cy="12" r="4" fill="currentColor" stroke="none" />
      </svg>
    ),
  },
  {
    value: 'upload',
    label: 'Upload',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
      </svg>
    ),
  },
]

export default function HomePage() {
  const [tab, setTab] = useState<Tab>('record')

  return (
    <main className="relative min-h-screen bg-[#0a0a0a] overflow-hidden flex flex-col">
      {/* Ambient glow */}
      <div className="pointer-events-none absolute inset-0 z-0" aria-hidden="true">
        <div
          className="absolute top-[-20%] left-[50%] translate-x-[-50%] h-[600px] w-[800px] rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(34,197,94,0.06) 0%, transparent 70%)',
            filter: 'blur(40px)',
          }}
        />
      </div>

      <div className="relative z-10 flex flex-col items-center px-4 pt-24 pb-16">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-8 flex items-center gap-2 rounded-full border border-[#22c55e]/20 bg-[#22c55e]/5 px-4 py-1.5"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-[#22c55e] animate-pulse" />
          <span className="text-xs font-medium text-[#22c55e] tracking-wider uppercase">
            AI Swing Analysis
          </span>
        </motion.div>

        {/* Hero headline */}
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
          className="text-center font-bold text-white mb-4"
          style={{
            fontSize: 'clamp(2.5rem, 8vw, 4.5rem)',
            lineHeight: 1.05,
            letterSpacing: '-0.03em',
          }}
        >
          Analyze Your{' '}
          <span style={{ color: '#22c55e' }}>Golf Swing</span>
        </motion.h1>

        {/* Subheading */}
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
          className="text-center text-gray-400 text-lg mb-10 max-w-md leading-relaxed"
        >
          Record or upload your swing. AI detects mechanical faults and delivers
          personalized coaching in seconds.
        </motion.p>

        {/* Tab switcher */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
          className="mb-6 flex rounded-xl bg-[#111111] border border-white/10 p-1 gap-1"
        >
          {TABS.map(({ value, label, icon }) => (
            <button
              key={value}
              type="button"
              onClick={() => setTab(value)}
              className={[
                'relative flex items-center gap-2 rounded-lg px-5 py-2 text-sm font-medium transition-colors duration-150',
                tab === value ? 'text-black' : 'text-gray-500 hover:text-gray-300',
              ].join(' ')}
            >
              {tab === value && (
                <motion.span
                  layoutId="tab-pill"
                  className="absolute inset-0 rounded-lg bg-[#22c55e]"
                  transition={{ type: 'spring', stiffness: 400, damping: 35 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-1.5">
                {icon}
                {label}
              </span>
            </button>
          ))}
        </motion.div>

        {/* Tab content */}
        <div className="w-full max-w-xl">
          <AnimatePresence mode="wait">
            {tab === 'record' ? (
              <motion.div
                key="record"
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 12 }}
                transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
              >
                <VideoRecorder />
              </motion.div>
            ) : (
              <motion.div
                key="upload"
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -12 }}
                transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
              >
                <VideoUpload />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Feature tags */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mt-16 flex flex-wrap justify-center gap-3"
        >
          {['X-Factor Analysis', 'Early Extension', 'Reverse Pivot', 'Swing Path'].map((tag) => (
            <span
              key={tag}
              className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-gray-500"
            >
              {tag}
            </span>
          ))}
        </motion.div>
      </div>
    </main>
  )
}
