import { describe, it, expect } from 'vitest'
import { isTypingTarget, SHORTCUT_GROUPS } from './keyboard'

/** Build a KeyboardEvent with a controlled `target` (jsdom-friendly). */
function keydown(target: EventTarget | null) {
  const event = new KeyboardEvent('keydown', { key: 'c', bubbles: true })
  if (target) Object.defineProperty(event, 'target', { value: target })
  return event
}

function makeEl(tag: string, opts: { contentEditable?: boolean } = {}) {
  const el = document.createElement(tag)
  if (opts.contentEditable) {
    // jsdom does not compute `isContentEditable` from the attribute; mirror the
    // real DOM behaviour so the helper's check is exercised correctly.
    Object.defineProperty(el, 'isContentEditable', { value: true, configurable: true })
  }
  document.body.append(el)
  return el
}

describe('isTypingTarget', () => {
  it('returns true for INPUT elements', () => {
    expect(isTypingTarget(keydown(makeEl('input')))).toBe(true)
  })

  it('returns true for TEXTAREA elements', () => {
    expect(isTypingTarget(keydown(makeEl('textarea')))).toBe(true)
  })

  it('returns true for SELECT elements', () => {
    expect(isTypingTarget(keydown(makeEl('select')))).toBe(true)
  })

  it('returns true for contentEditable elements', () => {
    expect(isTypingTarget(keydown(makeEl('div', { contentEditable: true })))).toBe(true)
  })

  it('returns false for plain DIV/button elements', () => {
    expect(isTypingTarget(keydown(makeEl('div')))).toBe(false)
    expect(isTypingTarget(keydown(makeEl('button')))).toBe(false)
  })

  it('returns false when target is not an HTMLElement (e.g. window)', () => {
    expect(isTypingTarget(keydown(null))).toBe(false)
  })
})

describe('SHORTCUT_GROUPS', () => {
  it('documents every M4 shortcut the provider handles', () => {
    const all = SHORTCUT_GROUPS.flatMap((g) => g.items.map((i) => i.keys))
    // VAL-SHORTCUTS-001..007 coverage in the help reference.
    expect(all).toEqual(expect.arrayContaining(['⌘K', 'C', 'G I', '[', ']', 'Esc', '?']))
  })

  it('every item has a non-empty description', () => {
    for (const group of SHORTCUT_GROUPS) {
      for (const item of group.items) {
        expect(item.description.trim().length).toBeGreaterThan(0)
      }
    }
  })
})
