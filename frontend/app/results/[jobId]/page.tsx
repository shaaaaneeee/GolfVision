'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { getResult, AnalysisResult } from '@/lib/api'
import FaultCard from '@/components/FaultCard'
import CoachingPanel from '@/components/CoachingPanel'

const POLL_INTERVAL = 2000

function LoadingState({ status }: { status: string }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col items-center gap-6 py-24 text-center"
    >
      {/* Animated dots */}
      <div className="flex gap-2">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="h-2 w-2 rounded-full bg-[#22c55e]"
            animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1.2, 0.8] }}
            transition={{
              duration: 1.2,
              repeat: Infinity,
              delay: i * 0.2,
              ease: 'easeInOut',
            }}
          />
        ))}
      </div>
      <div>
        <p className="text-lg font-semibold text-white">Analyzing your swing…</p>
        <p className="text-sm text-gray-500 mt-1 capitalize">{status}</p>
      </div>
    </motion.div>
  )
}

function FailedState({ error }: { error: string | null }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="flex flex-col items-center gap-6 py-24 text-center"
    >
      <div className="h-16 w-16 rounded-full bg-red-500/10 flex items-center justify-center ring-1 ring-red-500/20">
        <svg
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#ef4444"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <div>
        <p className="text-lg font-semibold text-white mb-1">Analysis Failed</p>
        <p className="text-sm text-red-400">{error ?? 'An unexpected error occurred.'}</p>
      </div>
      <Link
        href="/"
        className="rounded-xl bg-white/5 border border-white/10 px-6 py-2.5 text-sm font-medium text-white hover:bg-white/10 transition-colors"
      >
        ← Try Again
      </Link>
    </motion.div>
  )
}

function NoFaultsState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center gap-4 py-20 text-center"
    >
      <div className="h-16 w-16 rounded-full bg-[#22c55e]/10 flex items-center justify-center ring-1 ring-[#22c55e]/20">
        <svg
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#22c55e"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
          <polyline points="22 4 12 14.01 9 11.01" />
        </svg>
      </div>
      <p className="text-xl font-semibold text-white">Great swing!</p>
      <p className="text-gray-400 text-sm max-w-xs">
        No mechanical faults detected. Keep up the excellent form.
      </p>
    </motion.div>
  )
}

export default function ResultsPage() {
  const params = useParams<{ jobId: string }>()
  const jobId = params.jobId
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  function stopPolling() {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  const fetchOnce = useCallback(async () => {
    try {
      const data = await getResult(jobId)
      setResult(data)
      if (data.status === 'complete' || data.status === 'failed') {
        stopPolling()
      }
    } catch (err) {
      setFetchError(err instanceof Error ? err.message : 'Failed to fetch result')
      stopPolling()
    }
  }, [jobId])

  useEffect(() => {
    fetchOnce()
    const id = setInterval(fetchOnce, POLL_INTERVAL)
    intervalRef.current = id
    return () => clearInterval(id)
  }, [fetchOnce])

  const isLoading = !result || result.status === 'queued' || result.status === 'processing'
  const isFailed = result?.status === 'failed' || !!fetchError
  const isComplete = result?.status === 'complete'

  return (
    <main className="min-h-screen bg-[#0a0a0a]">
      {/* Ambient glow */}
      <div className="pointer-events-none fixed inset-0 z-0" aria-hidden="true">
        <div
          className="absolute top-[-10%] left-[50%] translate-x-[-50%] h-[500px] w-[700px] rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(34,197,94,0.04) 0%, transparent 70%)',
            filter: 'blur(40px)',
          }}
        />
      </div>

      <div className="relative z-10 mx-auto max-w-2xl px-4 pt-12 pb-24">
        {/* Back link */}
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-white transition-colors mb-10 group"
        >
          <span className="group-hover:-translate-x-0.5 transition-transform inline-block">
            ←
          </span>
          Back to Upload
        </Link>

        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-10"
        >
          <h1
            className="font-bold tracking-tight text-white mb-1"
            style={{ fontSize: 'clamp(1.75rem, 5vw, 2.25rem)', letterSpacing: '-0.02em' }}
          >
            Swing Analysis
          </h1>
          <p className="text-xs text-gray-600 font-mono break-all">{jobId}</p>
        </motion.div>

        {/* States */}
        <AnimatePresence mode="wait">
          {fetchError ? (
            <FailedState key="fetch-error" error={fetchError} />
          ) : isLoading ? (
            <LoadingState key="loading" status={result?.status ?? 'queued'} />
          ) : isFailed ? (
            <FailedState key="failed" error={result?.error ?? null} />
          ) : isComplete && result ? (
            <motion.div
              key="complete"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
              className="flex flex-col gap-8"
            >
              {/* Faults section */}
              <section>
                <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">
                  Detected Faults
                </h2>
                {!result.faults || result.faults.length === 0 ? (
                  <NoFaultsState />
                ) : (
                  <div className="flex flex-col gap-3">
                    {result.faults.map((f, i) => (
                      <FaultCard
                        key={f.name}
                        fault={f.name}
                        severity={f.severity}
                        index={i}
                      />
                    ))}
                  </div>
                )}
              </section>

              {/* Coaching section */}
              {result.coaching && (
                <section>
                  <CoachingPanel coaching={result.coaching} />
                </section>
              )}
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>
    </main>
  )
}
