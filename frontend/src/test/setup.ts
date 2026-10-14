import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'

import { mockApi } from './mockApi'

// jsdom lacks these browser APIs used by the UI.
HTMLDialogElement.prototype.showModal ??= function showModal(this: HTMLDialogElement) {
  this.setAttribute('open', '')
}
HTMLDialogElement.prototype.close ??= function close(this: HTMLDialogElement) {
  this.removeAttribute('open')
}

beforeEach(() => {
  mockApi() // anonymous visitor with a healthy backend; tests override as needed
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})
