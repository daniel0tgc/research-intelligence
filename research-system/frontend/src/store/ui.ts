import { create } from 'zustand'

type ActiveView = 'graph' | 'agenda' | 'concepts' | 'gaps'

interface UiStore {
  sidePanelOpen: boolean
  chatOpen: boolean
  activeView: ActiveView
  setSidePanelOpen: (open: boolean) => void
  setChatOpen: (open: boolean) => void
  setActiveView: (view: ActiveView) => void
}

export const useUiStore = create<UiStore>((set) => ({
  sidePanelOpen: false,
  chatOpen: false,
  activeView: 'graph',
  setSidePanelOpen: (open) => set({ sidePanelOpen: open }),
  setChatOpen: (open) => set({ chatOpen: open }),
  setActiveView: (view) => set({ activeView: view }),
}))
