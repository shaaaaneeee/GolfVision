import React from 'react'
import { render, screen } from '@testing-library/react'
import FaultCard from '@/components/FaultCard'

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
      <div {...props}>{children}</div>
    ),
  },
}))

describe('FaultCard', () => {
  it('renders the display_name of the fault', () => {
    render(
      <FaultCard
        fault="early_extension"
        severity={0.8}
        index={0}
      />
    )
    expect(screen.getByText('Early Extension')).toBeInTheDocument()
  })

  it('renders severity as a percentage', () => {
    render(
      <FaultCard
        fault="reverse_pivot"
        severity={0.65}
        index={1}
      />
    )
    expect(screen.getByText('65%')).toBeInTheDocument()
  })

  it('applies green color class for severity < 0.4', () => {
    render(
      <FaultCard
        fault="insufficient_x_factor"
        severity={0.3}
        index={0}
      />
    )
    const bar = document.querySelector('[data-testid="severity-bar"]')
    expect(bar?.className).toMatch(/green|low/)
  })

  it('applies amber color class for severity 0.4-0.7', () => {
    render(
      <FaultCard
        fault="early_extension"
        severity={0.55}
        index={0}
      />
    )
    const bar = document.querySelector('[data-testid="severity-bar"]')
    expect(bar?.className).toMatch(/amber|yellow|mid/)
  })

  it('applies red color class for severity > 0.7', () => {
    render(
      <FaultCard
        fault="reverse_pivot"
        severity={0.85}
        index={0}
      />
    )
    const bar = document.querySelector('[data-testid="severity-bar"]')
    expect(bar?.className).toMatch(/red|high/)
  })
})
