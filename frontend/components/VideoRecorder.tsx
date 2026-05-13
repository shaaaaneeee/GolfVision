'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { submitVideo, SkillLevel } from '@/lib/api'

// MediaPipe types (loaded dynamically to avoid SSR issues)
type PoseLandmarkerType = import('@mediapipe/tasks-vision').PoseLandmarker
type DrawingUtilsType = import('@mediapipe/tasks-vision').DrawingUtils

const WASM_PATH = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm'
const MODEL_PATH =
  'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task'

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
  return `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`
}

type Phase = 'idle' | 'loading' | 'live' | 'recording' | 'review'

export default function VideoRecorder() {
  const router = useRouter()

  // DOM refs
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const playbackRef = useRef<HTMLVideoElement>(null)

  // MediaPipe refs
  const landmarkerRef = useRef<PoseLandmarkerType | null>(null)
  const drawingUtilsRef = useRef<DrawingUtilsType | null>(null)
  const rafRef = useRef<number | null>(null)
  const lastVideoTimeRef = useRef(-1)

  // Recording refs
  const streamRef = useRef<MediaStream | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // State
  const [phase, setPhase] = useState<Phase>('idle')
  const [elapsed, setElapsed] = useState(0)
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null)
  const [recordedUrl, setRecordedUrl] = useState<string | null>(null)
  const [skill, setSkill] = useState<SkillLevel>('intermediate')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [poseLoaded, setPoseLoaded] = useState(false)
  const [permissionDenied, setPermissionDenied] = useState(false)

  // ── MediaPipe skeleton draw loop ──────────────────────────────────────────
  const drawLoop = useCallback(() => {
    const video = videoRef.current
    const canvas = canvasRef.current
    const landmarker = landmarkerRef.current
    const drawUtils = drawingUtilsRef.current

    if (!video || !canvas || !landmarker || !drawUtils || video.readyState < 2) {
      rafRef.current = requestAnimationFrame(drawLoop)
      return
    }

    if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
      canvas.width = video.videoWidth || 640
      canvas.height = video.videoHeight || 480
    }

    const ctx = canvas.getContext('2d')!
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    if (video.currentTime !== lastVideoTimeRef.current) {
      lastVideoTimeRef.current = video.currentTime
      const result = landmarker.detectForVideo(video, performance.now())

      if (result.landmarks.length > 0) {
        const { PoseLandmarker } = require('@mediapipe/tasks-vision') as typeof import('@mediapipe/tasks-vision')

        // Golf-relevant connections only: torso, arms, legs — skip face & fingers
        // Landmark indices: 11-16 = shoulders/elbows/wrists, 23-28 = hips/knees/ankles
        const GOLF_CONNECTIONS = PoseLandmarker.POSE_CONNECTIONS.filter(
          ({ start, end }: { start: number; end: number }) =>
            start >= 11 && start <= 28 && end >= 11 && end <= 28
        )

        for (const landmarks of result.landmarks) {
          // Pass 1 — wide soft glow
          ctx.filter = 'blur(3px)'
          drawUtils.drawConnectors(landmarks, GOLF_CONNECTIONS, {
            color: 'rgba(34,197,94,0.55)',
            lineWidth: 10,
          })
          ctx.filter = 'none'

          // Pass 2 — crisp bright line
          drawUtils.drawConnectors(landmarks, GOLF_CONNECTIONS, {
            color: '#22c55e',
            lineWidth: 3,
          })

          // Joint dots — white circle with green fill, dark outline for contrast
          drawUtils.drawLandmarks(
            landmarks.filter((_: unknown, i: number) => i >= 11 && i <= 28),
            {
              color: '#000000',
              fillColor: '#ffffff',
              lineWidth: 2,
              radius: 6,
            }
          )
          // Inner green fill
          drawUtils.drawLandmarks(
            landmarks.filter((_: unknown, i: number) => i >= 11 && i <= 28),
            {
              color: 'transparent',
              fillColor: '#22c55e',
              lineWidth: 0,
              radius: 4,
            }
          )
        }
      }
    }

    rafRef.current = requestAnimationFrame(drawLoop)
  }, [])

  // ── Load MediaPipe ────────────────────────────────────────────────────────
  const loadMediaPipe = useCallback(async () => {
    try {
      const { FilesetResolver, PoseLandmarker, DrawingUtils } =
        await import('@mediapipe/tasks-vision')

      const vision = await FilesetResolver.forVisionTasks(WASM_PATH)

      const landmarker = await PoseLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: MODEL_PATH,
          delegate: 'GPU',
        },
        runningMode: 'VIDEO',
        numPoses: 1,
        minPoseDetectionConfidence: 0.5,
        minPosePresenceConfidence: 0.5,
        minTrackingConfidence: 0.5,
      })

      landmarkerRef.current = landmarker
      const canvas = canvasRef.current
      if (canvas) {
        const ctx = canvas.getContext('2d')!
        drawingUtilsRef.current = new DrawingUtils(ctx)
      }
      setPoseLoaded(true)
    } catch {
      // Pose overlay unavailable — continue without it
      setPoseLoaded(false)
    }
  }, [])

  // ── Start camera ──────────────────────────────────────────────────────────
  const startCamera = useCallback(async () => {
    setError(null)
    setPermissionDenied(false)
    setPhase('loading')

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      })
      streamRef.current = stream
      setPhase('live')

      // Load MediaPipe in parallel (non-blocking)
      loadMediaPipe()
    } catch (err) {
      setPhase('idle')
      if (err instanceof Error && err.name === 'NotAllowedError') {
        setPermissionDenied(true)
      } else {
        setError('Could not access camera. Check browser permissions.')
      }
    }
  }, [loadMediaPipe])

  // Attach stream to video + start draw loop when phase becomes live/recording
  useEffect(() => {
    if ((phase === 'live' || phase === 'recording') && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current
      // Start skeleton draw loop
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      rafRef.current = requestAnimationFrame(drawLoop)
    }
    if (phase !== 'live' && phase !== 'recording') {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
        rafRef.current = null
      }
    }
  }, [phase, drawLoop])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop())
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      if (timerRef.current) clearInterval(timerRef.current)
      landmarkerRef.current?.close()
    }
  }, [])

  // ── Recording controls ────────────────────────────────────────────────────
  function startRecording() {
    if (!streamRef.current) return
    chunksRef.current = []
    const mimeType = getSupportedMimeType()
    const mr = new MediaRecorder(streamRef.current, { mimeType })
    mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
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
        if (prev + 1 >= MAX_SECONDS) { stopRecording(); return prev + 1 }
        return prev + 1
      })
    }, 1000)
  }

  function stopRecording() {
    if (mediaRecorderRef.current?.state === 'recording') mediaRecorderRef.current.stop()
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null }
  }

  function retake() {
    if (recordedUrl) { URL.revokeObjectURL(recordedUrl); setRecordedUrl(null) }
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
    const file = new File([recordedBlob], `swing.${ext}`, { type: recordedBlob.type })
    try {
      const { job_id } = await submitVideo(file, skill)
      streamRef.current?.getTracks().forEach((t) => t.stop())
      router.push(`/results/${job_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setLoading(false)
    }
  }

  const progress = (elapsed / MAX_SECONDS) * 100

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-xl mx-auto flex flex-col gap-6"
    >
      {/* Viewport */}
      <div className="relative overflow-hidden rounded-2xl bg-[#111111] border border-white/10 aspect-video">

        {/* Live camera + canvas overlay (always mounted when live/recording) */}
        <div
          className={`absolute inset-0 transition-opacity duration-300 ${
            phase === 'live' || phase === 'recording' ? 'opacity-100' : 'opacity-0 pointer-events-none'
          }`}
        >
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
          {/* Skeleton overlay canvas */}
          <canvas
            ref={canvasRef}
            className="absolute inset-0 w-full h-full"
            style={{ objectFit: 'cover' }}
          />

          {/* Alignment grid (live only) */}
          {phase === 'live' && (
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute inset-0 grid grid-cols-3 grid-rows-3">
                {Array.from({ length: 9 }).map((_, i) => (
                  <div key={i} className="border border-white/[0.07]" />
                ))}
              </div>
              <div className="absolute bottom-3 left-0 right-0 flex justify-center">
                <span className="rounded-full bg-black/50 backdrop-blur-sm px-3 py-1 text-xs text-white/50">
                  Face-on · hip height · 8–12 ft away
                </span>
              </div>
              {/* MediaPipe loading indicator */}
              {!poseLoaded && (
                <div className="absolute top-3 right-3 flex items-center gap-1.5 rounded-full bg-black/50 backdrop-blur-sm px-2.5 py-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#22c55e] animate-pulse" />
                  <span className="text-[10px] text-white/50">Loading skeleton…</span>
                </div>
              )}
            </div>
          )}

          {/* Recording HUD */}
          {phase === 'recording' && (
            <div className="absolute top-3 left-3 right-3 flex items-center gap-2 pointer-events-none">
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
              <span className="text-xs text-white/50 font-mono tabular-nums">
                -{formatTime(MAX_SECONDS - elapsed)}
              </span>
            </div>
          )}
        </div>

        {/* Idle / Loading / Review states */}
        <AnimatePresence>
          {phase === 'idle' && (
            <motion.div
              key="idle"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="absolute inset-0 flex flex-col items-center justify-center gap-4 px-8 text-center"
            >
              {permissionDenied ? (
                <>
                  <div className="h-12 w-12 rounded-xl bg-red-500/10 flex items-center justify-center">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                  </div>
                  <p className="text-sm text-red-400">Camera access denied. Enable it in your browser settings.</p>
                  <button onClick={startCamera} className="rounded-lg bg-white/5 border border-white/10 px-4 py-2 text-sm text-white hover:bg-white/10 transition-colors">
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
                    <p className="text-sm font-medium text-white mb-1">Live skeleton tracking</p>
                    <p className="text-xs text-gray-500">Real-time pose overlay · record when ready</p>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                    onClick={startCamera}
                    className="rounded-xl bg-[#22c55e] text-black text-sm font-semibold px-6 py-2.5 shadow-[0_0_20px_rgba(34,197,94,0.3)] hover:bg-[#16a34a] transition-colors"
                  >
                    Enable Camera
                  </motion.button>
                </>
              )}
            </motion.div>
          )}

          {phase === 'loading' && (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="absolute inset-0 flex items-center justify-center"
            >
              <div className="h-8 w-8 rounded-full border-2 border-[#22c55e]/30 border-t-[#22c55e] animate-spin" />
            </motion.div>
          )}

          {phase === 'review' && recordedUrl && (
            <motion.div
              key="review"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="absolute inset-0"
            >
              {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
              <video ref={playbackRef} src={recordedUrl} controls loop className="w-full h-full object-cover" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Controls below viewport */}
      <AnimatePresence mode="wait">
        {(phase === 'live' || phase === 'recording') && (
          <motion.div
            key="rec-controls"
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }}
            className="flex items-center justify-center gap-6"
          >
            {/* Spacer (mirrors the stop/cancel button) */}
            <div className="w-10" />

            {/* Record / Stop button */}
            {phase === 'live' ? (
              <motion.button
                whileHover={{ scale: 1.08 }} whileTap={{ scale: 0.92 }}
                onClick={startRecording}
                className="h-16 w-16 rounded-full bg-red-500 shadow-[0_0_30px_rgba(239,68,68,0.45)] hover:bg-red-400 transition-colors flex items-center justify-center"
                aria-label="Start recording"
              >
                <span className="h-5 w-5 rounded-full bg-white" />
              </motion.button>
            ) : (
              <motion.button
                whileHover={{ scale: 1.08 }} whileTap={{ scale: 0.92 }}
                onClick={stopRecording}
                className="h-16 w-16 rounded-full bg-red-500 shadow-[0_0_40px_rgba(239,68,68,0.6)] hover:bg-red-400 transition-colors flex items-center justify-center"
                aria-label="Stop recording"
              >
                <span className="h-5 w-5 rounded-md bg-white" />
              </motion.button>
            )}

            {/* Cancel back to idle */}
            <button
              onClick={() => {
                streamRef.current?.getTracks().forEach((t) => t.stop())
                if (rafRef.current) cancelAnimationFrame(rafRef.current)
                setPhase('idle')
              }}
              className="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
              aria-label="Stop camera"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </motion.div>
        )}

        {phase === 'review' && (
          <motion.div
            key="review-controls"
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }}
            className="flex flex-col gap-4"
          >
            {/* Skill selector */}
            <div className="flex gap-2">
              {SKILL_LEVELS.map(({ value, label }) => (
                <button
                  key={value} type="button" onClick={() => setSkill(value)}
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

            <AnimatePresence>
              {error && (
                <motion.p initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="text-sm text-red-400 text-center">
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            <div className="flex gap-3">
              <button type="button" onClick={retake} className="flex-1 rounded-xl py-3.5 text-sm font-semibold bg-white/5 text-gray-300 hover:bg-white/10 border border-white/10 transition-all">
                Retake
              </button>
              <motion.button
                type="button" onClick={onSubmit} disabled={loading}
                whileHover={!loading ? { scale: 1.02 } : {}} whileTap={!loading ? { scale: 0.98 } : {}}
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
                ) : 'Analyze Swing'}
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
