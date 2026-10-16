export default function Header({ modelStatus = {} }) {
  const status = modelStatus.status || 'unloaded'
  const ready = status === 'ready'
  const error = status === 'error'
  const loading = status === 'loading' || status === 'unloaded'

  let label = 'Waiting for local model…'
  if (ready) {
    const bits = [modelStatus.gpu || 'GPU']
    if (modelStatus.dtype) bits.push(modelStatus.dtype)
    bits.push('ready')
    label = bits.join(' · ')
  } else if (status === 'loading') {
    label = `Loading ${modelStatus.model_id || 'Music Flamingo'}…`
  } else if (error) {
    label = modelStatus.error || 'Model failed to load'
  }

  return (
    <header className="border-b border-slate-800/50">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-coral-500 to-coral-600 flex items-center justify-center shadow-lg shadow-coral-500/25">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Vocal Critic</h1>
            <p className="text-xs text-slate-500">Local Music Flamingo on your GPU</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-sm min-w-0">
          <span
            className={`w-2 h-2 rounded-full flex-shrink-0 ${
              ready ? 'bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.15)]' : ''
            } ${loading ? 'bg-amber-400 animate-pulse' : ''} ${error ? 'bg-red-500' : ''}`}
          />
          <span className="text-slate-400 truncate" title={label}>{label}</span>
        </div>
      </div>
    </header>
  )
}
