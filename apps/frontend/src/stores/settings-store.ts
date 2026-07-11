import { create } from 'zustand'

interface SettingsState {
  activeSection: string
  setActiveSection: (section: string) => void
}

export const useSettingsStore = create<SettingsState>((set) => ({
  activeSection: 'profile',
  setActiveSection: (activeSection) => set({ activeSection }),
}))
