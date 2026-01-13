export default function LoadingState() {
  return (
    <div className="glass-card rounded-2xl p-12 text-center">
      {/* Animated waveform */}
      <div className="flex items-end justify-center gap-1 h-16 mb-8">
        {[...Array(12)].map((_, i) => (
          <div
            key={i}
            className="loading-bar w-2 bg-gradient-to-t from-coral-600 to-coral-400 rounded-full"
            style={{
              height: `${Math.random() * 60 + 20}%`,
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
      </div>

      <h3 className="text-xl font-semibold text-white mb-3">
        Analyzing Your Performance
      </h3>
      
      <p className="text-slate-400 mb-6 max-w-md mx-auto">
        Our AI is listening carefully to your recording, evaluating pitch accuracy, 
        timing, expression, and technique...
      </p>

      {/* Progress steps */}
      <div className="flex flex-col gap-3 max-w-xs mx-auto text-left">
        <ProgressStep label="Processing audio" status="complete" />
        <ProgressStep label="Analyzing pitch & timing" status="active" />
        <ProgressStep label="Evaluating expression" status="pending" />
        <ProgressStep label="Generating feedback" status="pending" />
      </div>

      <p className="text-xs text-slate-500 mt-8">
        This may take 30-60 seconds depending on the length of your recording
      </p>
    </div>
  )
}

function ProgressStep({ label, status }) {
  return (
    <div className="flex items-center gap-3">
      <div className={`
        w-5 h-5 rounded-full flex items-center justify-center
        ${status === 'complete' ? 'bg-emerald-500' : ''}
        ${status === 'active' ? 'bg-coral-500 animate-pulse' : ''}
        ${status === 'pending' ? 'bg-slate-700' : ''}
      `}>
        {status === 'complete' && (
          <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        )}
        {status === 'active' && (
          <div className="w-2 h-2 bg-white rounded-full" />
        )}
      </div>
      <span className={`text-sm ${status === 'pending' ? 'text-slate-500' : 'text-slate-300'}`}>
        {label}
      </span>
    </div>
  )
}

