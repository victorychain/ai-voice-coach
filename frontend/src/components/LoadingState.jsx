export default function LoadingState({ liveText = '' }) {
  return (
    <div className="glass-card rounded-2xl p-12 text-center">
      <div className="flex items-end justify-center gap-1 h-16 mb-8">
        {[...Array(12)].map((_, i) => (
          <div
            key={i}
            className="loading-bar w-2 bg-gradient-to-t from-coral-600 to-coral-400 rounded-full"
            style={{
              height: `${20 + ((i * 17) % 60)}%`,
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
      </div>

      <h3 className="text-xl font-semibold text-white mb-3">
        Listening on the local GPU
      </h3>

      <p className="text-slate-400 mb-6 max-w-md mx-auto">
        Music Flamingo is reading the audio in 30-second windows.
        First load after launch is slower while the 8B checkpoint sits in VRAM.
      </p>

      {liveText ? (
        <p className="text-xs text-slate-500">Streaming tokens…</p>
      ) : (
        <p className="text-xs text-slate-500">
          This may take 30–90 seconds depending on the length of the recording
        </p>
      )}
    </div>
  )
}
