export default function Header() {
  return (
    <header className="border-b border-slate-800/50">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Logo */}
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-coral-500 to-coral-600 flex items-center justify-center shadow-lg shadow-coral-500/25">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Vocal Critic</h1>
            <p className="text-xs text-slate-500">AI Singing Coach</p>
          </div>
        </div>

        {/* Status indicator */}
        <div className="flex items-center gap-2 text-sm">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-slate-400">Model Ready</span>
        </div>
      </div>
    </header>
  )
}

