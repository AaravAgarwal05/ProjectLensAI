/** Error thrown by placeholder service methods. */
export class NotImplementedError extends Error {
  constructor(service: string, method: string) {
    super(`${service}.${method} — not implemented. Wire to real API when backend is ready.`)
    this.name = 'NotImplementedError'
  }
}
