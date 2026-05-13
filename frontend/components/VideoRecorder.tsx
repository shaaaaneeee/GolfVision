'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { submitVideo, SkillLevel } from '@/lib/api'

const SKILL_LEVELS: { value: SkillLevel; label: string }[] = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
]

const MAX_SECONDS = 30

function getSupportedMimeType(): string {
  const candidates = ['video/webm;codecs=vp9', 'video/webm;codecs=vp8', 'video/webm', 'video/mp4']
  return candidates.find((t) => MediaRecorder.isTypeSupported(t)) ?? 'video/webm'
}

function formatTime(s: number) {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${sec.toString().padStart(2, '0')}`
}

type Phase = 'idle' | 'live' | 'recording' | 'review'

export default function VideoRecorder() {
  const router = useRouter()
  const liveRef = useRef<HTMLVideoElement>(null)
  const playbackRef = useRef<HTMLVideoElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const [phase, setPhase] = useState<Phase>('idle')
  const [elapsed, setElapsed] = useState(0)
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null)
  const [recordedUrl, setRecordedUrl] = useState<string | null>(null)
  const [skill, setSkill] = useState<SkillLevel>('intermediate')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [permissionDenied, setPermissionDenied] = useState(false)

  // Attach stream to live video element whenever phase becomes live/recording
  useEffect(() => {
    if ((phase === 'live' || phase === 'recording') && liveRef.current && streamRef.current) {
      liveRef.current.srcObject = streamRef.current
    }
  }, [phase])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop())
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  const startCamera = useCallback(async () => {
    setError(null)
    setPermissionDenied(false)
    try {
      const s = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      })
      streamRef.current = s
      setPhase('live')
    } catch (err) {
      if (err instanceof Error && err.name === 'NotAllowedError') {
        setPermissionDenied(true)
      } else {
        setError('Could not access camera. Check browser permissions.')
      }
    }
  }, [])

  function startRecording() {
    if (!streamRef.current) return
    chunksRef.current = []
    const mimeType = getSupportedMimeType()
    const mr = new MediaRecorder(streamRef.current, { mimeType })
    mr.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data)
    }
    mr.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mimeType })
      const url = URL.createObjectURL(blob)
      setRecordedBlob(blob)
      setRecordedUrl(url)
      setPhase('review')
    }
    mr.start(100)
    mediaRecorderRef.current = mr
    setElapsed(0)
    setPhase('recording')
    timerRef.current = setInterval(() => {
      setElapsed((prev) => {
        if (prev + 1 >= MAX_SECONDS) {
          stopRecording()
        }
        return prev + 1
      })
    }, 1000)
  }

  function stopRecording() {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

  function retake() {
    if (recordedUrl) {
      URL.revokeObjectURL(recordedUrl)
      setRecordedUrl(null)
    }
    setRecordedBlob(null)
    setElapsed(0)
    setError(null)
    setPhase('live')
  }

  async function onSubmit() {
    if (!recordedBlob) return
    setLoading(true)
    setError(null)
    const ext = getSupportedMimeType().includes('webm') ? 'webm' : 'mp4'
    const file = new File([recordedBlob], `swing_recording.${ext}`, { type: recordedBlob.type })
    try {
      const { job_id } = await submitVideo(file, skill)
      // Stop camera before navigating
      streamRef.current?.getTracks().forEach((t) => t.stop())
      router.push(`/results/${job_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setLoading(false)
    }
  }

  const remaining = MAX_SECONDS - elapsed
  const progress = (elapsed / MAX_SECONDS) * 100

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-xl mx-auto flex flex-col gap-6"
    >
      {/* Camera viewport */}
      <div className="relative overflow-hidden rounded-2xl bg-[#111111] border border-white/10 aspect-video">
        <AnimatePresence mode="wait">
          {phase === 'idle' && (
            <motion.div
              key="idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 flex flex-col items-center justify-center gap-4 px-8 text-center"
            >
              {permissionDenied ? (
                <>
                  <div className="h-12 w-12 rounded-xl bg-red-500/10 flex items-center justify-center">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="8" x2="12" y2="12" />
                      <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                  </div>
                  <p className="text-sm text-red-400">Camera access denied. Enable it in your browser settings, then try again.</p>
                  <button
                    onClick={startCamera}
                    className="rounded-lg bg-white/5 px-4 py-2 text-sm text-white hover:bg-white/10 transition-colors border border-white/10"
                  >
                    Try again
                  </button>
                </>
              ) : (
                <>
                  <div className="h-14 w-14 rounded-2xl bg-[#22c55e]/10 flex items-center justify-center">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white mb-1">Record your swing directly</p>
                    <p className="text-xs text-gray-500">Face-on angle, hip height, 8–12 ft away</p>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={startCamera}
                    className="rounded-xl bg-[#22c55e] text-black text-sm font-semibold px-6 py-2.5 shadow-[0_0_20px_rgba(34,197,94,0.3)] hover:bg-[#16a34a] transition-colors"
                  >
                    Enable Camera
                  </motion.button>
                </>
              )}
            </motion.div>
          )}

          {(phase === 'live' || phase === 'recording') && (
            <motion.div key="live" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0">
              {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
              <video
                ref={liveRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />
              {/* Recording indicator */}
              {phase === 'recording' && (
                <div className="absolute top-3 left-3 right-3 flex items-center gap-2">
                  <div className="flex items-center gap-1.5 rounded-full bg-black/60 backdrop-blur-sm px-3 py-1">
                    <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                    <span className="text-xs font-mono text-white">{formatTime(elapsed)}</span>
                  </div>
                  <div className="flex-1 h-1 rounded-full bg-white/20 overflow-hidden">
                    <motion.div
                      className="h-full bg-red-500"
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                  <span className="text-xs text-white/60 font-mono tabular-nums">-{formatTime(remaining)}</span>
                </div>
              )}
              {/* Grid alignment guide */}
              {phase === 'live' && (
                <div className="absolute inset-0 pointer-events-none">
                  <div className="absolute inset-0 grid grid-cols-3 grid-rows-3">
                    {Array.from({ length: 9 }).map((_, i) => (
                      <div key={i} className="border border-white/[0.06]" />
                    ))}
                  </div>
                  <div className="absolute bottom-3 left-0 right-0 flex justify-center">
                    <span className="rounded-full bg-black/50 backdrop-blur-sm px-3 py-1 text-xs text-white/50">
                      Align golfer in frame · face-on view
                    </span>
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {phase === 'review' && recordedUrl && (
            <motion.div key="review" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0">
              {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
              <video
                ref={playbackRef}
                src={recordedUrl}
                controls
                loop
                className="w-full h-full object-cover"
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Controls */}
      <AnimatePresence mode="wait">
        {phase === 'live' && (
          <motion.div key="live-ctrl" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex justify-center">
            <motion.button
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.94 }}
              onClick={startRecording}
              className="h-16 w-16 rounded-full bg-red-500 shadow-[0_0_30px_rgba(239,68,68,0.4)] hover:bg-red-400 transition-colors flex items-center justify-center"
              aria-label="Start recording"
            >
              <span className="h-5 w-5 rounded-full bg-white" />
            </motion.button>
          </motion.div>
        )}

        {phase === 'recording' && (
          <motion.div key="rec-ctrl" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex justify-center">
            <motion.button
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.94 }}
              onClick={stopRecording}
              className="h-16 w-16 rounded-full bg-red-500 shadow-[0_0_30px_rgba(239,68,68,0.5)] hover:bg-red-400 transition-colors flex items-center justify-center"
              aria-label="Stop recording"
            >
              <span className="h-5 w-5 rounded-md bg-white" />
            </motion.button>
          </motion.div>
        )}

        {phase === 'review' && (
          <motion.div key="review-ctrl" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex flex-col gap-4">
            {/* Skill level selector */}
            <div className="flex gap-2">
              {SKILL_LEVELS.map(({ value, label }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setSkill(value)}
                  className={[
                    'flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150',
                    skill === value
                      ? 'bg-[#22c55e] text-black shadow-[0_0_16px_rgba(34,197,94,0.3)]'
                      : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white border border-white/10',
                  ].join(' ')}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.p
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="text-sm text-red-400 text-center"
                >
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={retake}
                className="flex-1 rounded-xl py-3.5 text-sm font-semibold bg-white/5 text-gray-300 hover:bg-white/10 border border-white/10 transition-all"
              >
                Retake
              </button>
              <motion.button
                type="button"
                onClick={onSubmit}
                disabled={loading}
                whileHover={!loading ? { scale: 1.02 } : {}}
                whileTap={!loading ? { scale: 0.98 } : {}}
                className={[
                  'flex-[2] rounded-xl py-3.5 text-sm font-semibold tracking-wide transition-all duration-200',
                  !loading
                    ? 'bg-[#22c55e] text-black hover:bg-[#16a34a] shadow-[0_0_24px_rgba(34,197,94,0.25)]'
                    : 'bg-white/5 text-gray-600 cursor-not-allowed',
                ].join(' ')}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="h-3.5 w-3.5 rounded-full border-2 border-black/30 border-t-black animate-spin" />
                    Uploading…
                  </span>
                ) : (
                  'Analyze Swing'
                )}
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Global error (idle phase) */}
      {error && phase === 'idle' && (
        <p className="text-sm text-red-400 text-center">{error}</p>
      )}
    </motion.div>
  )
}
