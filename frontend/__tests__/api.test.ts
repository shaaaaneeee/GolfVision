import { submitVideo, getResult } from '@/lib/api'

const mockFetch = jest.fn()
global.fetch = mockFetch

beforeEach(() => {
  mockFetch.mockClear()
})

describe('submitVideo', () => {
  it('posts to /analyze with FormData and returns job_id', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ job_id: 'abc-123' }),
    })

    const file = new File(['content'], 'swing.mp4', { type: 'video/mp4' })
    const result = await submitVideo(file, 'beginner')

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/analyze',
      expect.objectContaining({ method: 'POST' })
    )
    expect(result).toEqual({ job_id: 'abc-123' })
  })

  it('throws an error when response is not ok', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'File too large' }),
    })

    const file = new File(['x'], 'swing.mp4', { type: 'video/mp4' })
    await expect(submitVideo(file, 'intermediate')).rejects.toThrow('File too large')
  })
})

describe('getResult', () => {
  it('fetches /result/:jobId and returns AnalysisResult', async () => {
    const mockResult = {
      job_id: 'abc-123',
      status: 'complete',
      faults: [{ name: 'early_extension', severity: 0.8, display_name: 'Early Extension' }],
      coaching: 'Keep your hips back.',
      features: {},
      error: null,
    }
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResult,
    })

    const result = await getResult('abc-123')
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/result/abc-123')
    expect(result).toEqual(mockResult)
  })

  it('throws when response is not ok', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Job not found' }),
    })

    await expect(getResult('bad-id')).rejects.toThrow('Job not found')
  })
})
