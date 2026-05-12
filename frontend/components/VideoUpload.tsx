'use client'

import { useState, useRef, DragEvent, ChangeEvent } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { submitVideo, SkillLevel } from '@/lib/api'

const SKILL_LEVELS: { value: SkillLevel; label: string }[] = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
]

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function VideoUpload() {
  const router = useRouter()
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [skill, setSkill] = useState<SkillLevel>('intermediate')
  const [isDragging, setIsDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function handleFile(f: File) {
    setFile(f)
    setError(null)
  }

  function onDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(true)
  }

  function onDragLeave() {
    setIsDragging(false)
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) handleFile(dropped)
  }

  function onInputChange(e: ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0]
    if (selected) handleFile(selected)
  }

  async function onSubmit() {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const { job_id } = await submitVideo(file, skill)
      router.push(`/results/${job_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-xl mx-auto flex flex-col gap-6"
    >
      {/* Drop zone */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={[
          'relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed',
          'min-h-[220px] cursor-pointer transition-all duration-200 select-none',
          isDragging
            ? 'border-[#22c55e] bg-[#22c55e]/5 shadow-[0_0_40px_rgba(34,197,94,0.15)]'
            : 'border-white/15 bg-[#111111] hover:border-[#22c55e]/50 hover:shadow-[0_0_30px_rgba(34,197,94,0.08)]',
        ].join(' ')}
      >
        <input
          ref={inputRef}
          type="file"
          accept="video/mp4,video/quicktime"
          className="hidden"
          onChange={onInputChange}
        />

        <AnimatePresence mode="wait">
          {file ? (
            <motion.div
              key="file-info"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="flex flex-col items-center gap-2 text-center px-6"
            >
              <div className="h-12 w-12 rounded-xl bg-[#22c55e]/10 flex items-center justify-center mb-1">
                <svg
                  width="22"
                  height="22"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#22c55e"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
                </svg>
              </div>
              <p className="text-sm font-medium text-white truncate max-w-[280px]">{file.name}</p>
              <p className="text-xs text-gray-500">{formatBytes(file.size)}</p>
              <p className="text-xs text-[#22c55e] mt-1">Click to change file</p>
            </motion.div>
          ) : (
            <motion.div
              key="drop-prompt"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-3 text-center px-6"
            >
              <div className="h-12 w-12 rounded-xl bg-white/5 flex items-center justify-center mb-1">
                <svg
                  width="22"
                  height="22"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#6b7280"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
                </svg>
              </div>
              <p className="text-sm font-medium text-white">Drag &amp; drop your swing video</p>
              <p className="text-xs text-gray-500">or click to browse — MP4 or MOV, max 50 MB</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

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

      {/* Submit button */}
      <motion.button
        type="button"
        disabled={!file || loading}
        onClick={onSubmit}
        whileHover={file && !loading ? { scale: 1.02 } : {}}
        whileTap={file && !loading ? { scale: 0.98 } : {}}
        className={[
          'w-full rounded-xl py-3.5 text-sm font-semibold tracking-wide transition-all duration-200',
          file && !loading
            ? 'bg-[#22c55e] text-black hover:bg-[#16a34a] shadow-[0_0_24px_rgba(34,197,94,0.25)] hover:shadow-[0_0_32px_rgba(34,197,94,0.4)]'
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
    </motion.div>
  )
}
