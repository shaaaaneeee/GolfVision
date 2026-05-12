'use client'

import { motion } from 'framer-motion'
import VideoUpload from '@/components/VideoUpload'

export default function HomePage() {
  return (
    <main className="relative min-h-screen bg-[#0a0a0a] overflow-hidden flex flex-col">
      {/* Ambient glow */}
      <div
        className="pointer-events-none absolute inset-0 z-0"
        aria-hidden="true"
      >
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
          className="text-center text-gray-400 text-lg mb-14 max-w-md leading-relaxed"
        >
          Upload your swing video. Our AI detects mechanical faults and delivers
          personalized coaching in seconds.
        </motion.p>

        {/* Upload component */}
        <div className="w-full max-w-xl">
          <VideoUpload />
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
