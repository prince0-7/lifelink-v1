import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import MemoryCard from './MemoryCard'

describe('MemoryCard', () => {
  const mockMemory = {
    id: '1',
    text: 'Test memory content',
    date: '2024-01-15',
    tag: 'Happy',
    image: null,
  }

  const mockOnDelete = vi.fn()

  it('renders memory content correctly', () => {
    render(<MemoryCard memory={mockMemory} onDelete={mockOnDelete} />)
    
    expect(screen.getByText('Test memory content')).toBeInTheDocument()
    expect(screen.getByText(/Happy/)).toBeInTheDocument()
    expect(screen.getByText(/2024-01-15/)).toBeInTheDocument()
  })

  it('calls onDelete when delete button is clicked', () => {
    render(<MemoryCard memory={mockMemory} onDelete={mockOnDelete} />)
    
    const deleteButton = screen.getByRole('button', { name: /delete/i })
    fireEvent.click(deleteButton)
    
    expect(mockOnDelete).toHaveBeenCalledWith('1')
  })

  it('renders image when provided', () => {
    const memoryWithImage = { ...mockMemory, image: 'data:image/png;base64,test' }
    render(<MemoryCard memory={memoryWithImage} onDelete={mockOnDelete} />)
    
    const image = screen.getByRole('img')
    expect(image).toHaveAttribute('src', 'data:image/png;base64,test')
  })
})
