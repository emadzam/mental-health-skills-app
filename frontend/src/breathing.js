// Pure pacing logic shared with meaningful boundary/interruption tests.
export const DURATION = 60
export function phaseAt(seconds) {
  const bounded = Math.max(0, seconds)
  const within = bounded % 10
  const inhale = within < 4
  return {
    phase: inhale ? 'Breathe in' : 'Breathe out',
    count: Math.min(inhale ? 4 : 6, Math.floor(inhale ? within : within - 4) + 1),
    total: inhale ? 4 : 6,
    cycle: Math.min(6, Math.floor(bounded / 10) + 1),
    scale: inhale ? 0.64 + (within / 4) * 0.36 : 1 - ((within - 4) / 6) * 0.36,
  }
}

export class Pacer {
  constructor(clock = () => performance.now()) {
    this.clock = clock
    this.accumulated = 0
    this.runningSince = null
    this.lastTick = null
  }
  start(seconds = 0) {
    this.accumulated = seconds
    this.runningSince = this.clock()
    this.lastTick = this.runningSince
  }
  elapsed() {
    return this.accumulated + (this.runningSince === null ? 0 : (this.clock() - this.runningSince) / 1000)
  }
  pause() {
    this.accumulated = this.elapsed()
    this.runningSince = null
    return this.accumulated
  }
  resume() {
    this.runningSince = this.clock()
    this.lastTick = this.runningSince
  }
  tick() {
    const current = this.clock()
    const gap = this.lastTick === null ? 0 : (current - this.lastTick) / 1000
    this.lastTick = current
    // A long blocked/background gap is an interruption, not six guided cycles.
    return { seconds: this.elapsed(), interrupted: gap > 2, complete: this.elapsed() >= DURATION }
  }
}
