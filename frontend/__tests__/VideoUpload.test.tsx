import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import VideoUpload from '@/components/VideoUpload'
import * as api from '@/lib/api'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
}))

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
      <div {...props}>{children}</div>
    ),
    button: ({
      children,
      whileHover: _wh,
      whileTap: _wt,
      ...props
    }: React.ButtonHTMLAttributes<HTMLButtonElement> & {
      whileHover?: unknown
      whileTap?: unknown
    }) => <button {...props}>{children}</button>,
    p: ({ children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
      <p {...props}>{children}</p>
    ),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// Mock the api module
jest.mock('@/lib/api', () => ({
  submitVideo: jest.fn(),
}))

describe('VideoUpload', () => {
  it('renders the drag-and-drop zone', () => {
    render(<VideoUpload />)
    expect(screen.getByText(/drag.*drop|upload.*video/i)).toBeInTheDocument()
  })

  it('renders all three skill level buttons', () => {
    render(<VideoUpload />)
    expect(screen.getByRole('button', { name: /beginner/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /intermediate/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /advanced/i })).toBeInTheDocument()
  })

  it('shows file name when a file is selected', async () => {
    render(<VideoUpload />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['video content'], 'my-swing.mp4', { type: 'video/mp4' })

    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText(/my-swing\.mp4/)).toBeInTheDocument()
    })
  })

  it('calls submitVideo on form submit with selected file and skill level', async () => {
    const mockSubmit = api.submitVideo as jest.MockedFunction<typeof api.submitVideo>
    mockSubmit.mockResolvedValueOnce({ job_id: 'test-job-123' })

    render(<VideoUpload />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['data'], 'swing.mp4', { type: 'video/mp4' })

    fireEvent.change(input, { target: { files: [file] } })

    // Select "Advanced"
    fireEvent.click(screen.getByRole('button', { name: /advanced/i }))

    // Submit
    const submitBtn = screen.getByRole('button', { name: /analyze/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith(file, 'advanced')
    })
  })

  it('shows error message when submitVideo throws', async () => {
    const mockSubmit = api.submitVideo as jest.MockedFunction<typeof api.submitVideo>
    mockSubmit.mockRejectedValueOnce(new Error('File too large'))

    render(<VideoUpload />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['data'], 'swing.mp4', { type: 'video/mp4' })

    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: /analyze/i }))

    await waitFor(() => {
      expect(screen.getByText(/file too large/i)).toBeInTheDocument()
    })
  })
})
