/**
 * Module-level singleton for blob URLs created from user-uploaded files.
 * Shared between DocumentZone (writer) and InsightSidebar (reader).
 * Not React state — blob URLs don't need to trigger re-renders.
 */
const store = new Map<string, string>()

export const blobStore = {
  set(name: string, file: File): void {
    const existing = store.get(name)
    if (existing) URL.revokeObjectURL(existing)
    store.set(name, URL.createObjectURL(file))
  },

  get(name: string): string | undefined {
    return store.get(name)
  },

  revoke(name: string): void {
    const url = store.get(name)
    if (url) {
      URL.revokeObjectURL(url)
      store.delete(name)
    }
  },

  clear(): void {
    for (const url of store.values()) URL.revokeObjectURL(url)
    store.clear()
  },
}
