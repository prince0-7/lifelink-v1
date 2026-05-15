import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

// Cleanup after each test case
afterEach(() => {
  cleanup()
})

// Mock window.speechSynthesis
globalThis.speechSynthesis = {
  speak: vi.fn(),
  cancel: vi.fn(),
  pause: vi.fn(),
  resume: vi.fn(),
  getVoices: vi.fn(() => []),
}

// Mock SpeechSynthesisUtterance
globalThis.SpeechSynthesisUtterance = vi.fn(() => ({
  text: '',
  lang: '',
  voice: null,
  volume: 1,
  rate: 1,
  pitch: 1,
}))

// Mock SpeechRecognition
globalThis.SpeechRecognition = globalThis.webkitSpeechRecognition = vi.fn(() => ({
  continuous: false,
  interimResults: false,
  lang: '',
  start: vi.fn(),
  stop: vi.fn(),
  abort: vi.fn(),
  onaudiostart: null,
  onaudioend: null,
  onend: null,
  onerror: null,
  onnomatch: null,
  onresult: null,
  onsoundstart: null,
  onsoundend: null,
  onspeechend: null,
  onstart: null,
}))
