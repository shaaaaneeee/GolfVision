import React from 'react'
import { render, screen } from '@testing-library/react'
import CoachingPanel from '@/components/CoachingPanel'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
      <div {...props}>{children}</div>
    ),
  },
}))

describe('CoachingPanel', () => {
  it('renders the coaching text', () => {
    render(<CoachingPanel coaching="Focus on keeping your hips square at impact." />)
    expect(
      screen.getByText('Focus on keeping your hips square at impact.')
    ).toBeInTheDocument()
  })

  it('renders a section heading', () => {
    render(<CoachingPanel coaching="Keep your head down through the shot." />)
    expect(screen.getByText(/coach/i)).toBeInTheDocument()
  })
})
