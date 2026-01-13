import { useState } from 'react'

export default function FeedbackDisplay({ feedback, audioUrl, onReset }) {
  const [activeTab, setActiveTab] = useState('analysis')
  
  const isDetailed = feedback.type === 'detailed' && feedback.aspects

  return (
    <div className="space-y-6">
      {/* Header with audio player */}
      <div className="glass-card rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="font-medium text-white">Analysis Complete</p>
              <p className="text-sm text-slate-400">{feedback.audio_file}</p>
            </div>
          </div>
          <button
            onClick={onReset}
            className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium transition-colors"
          >
            Analyze Another
          </button>
        </div>

        {audioUrl && (
          <audio 
            controls 
            src={audioUrl} 
            className="w-full h-12 rounded-lg"
            style={{ filter: 'sepia(20%) saturate(70%) grayscale(1) contrast(99%) invert(12%)' }}
          />
        )}
      </div>

      {/* Tabs for detailed analysis */}
      {isDetailed && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {Object.keys(feedback.aspects).map((aspect) => (
            <button
              key={aspect}
              onClick={() => setActiveTab(aspect)}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all
                ${activeTab === aspect 
                  ? 'bg-coral-500 text-white' 
                  : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
                }
              `}
            >
              {formatAspectName(aspect)}
            </button>
          ))}
        </div>
      )}

      {/* Feedback Content */}
      <div className="glass-card rounded-2xl p-6">
        {isDetailed ? (
          <div>
            <h2 className="text-xl font-semibold text-coral-400 mb-4 flex items-center gap-2">
              {getAspectIcon(activeTab)}
              {formatAspectName(activeTab)}
            </h2>
            <div className="feedback-content prose prose-invert max-w-none">
              <FormattedFeedback text={feedback.aspects[activeTab]} />
            </div>
          </div>
        ) : (
          <div>
            <h2 className="text-xl font-semibold text-coral-400 mb-4 flex items-center gap-2">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
              Comprehensive Analysis
            </h2>
            <div className="feedback-content prose prose-invert max-w-none">
              <FormattedFeedback text={feedback.analysis} />
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ActionCard
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          }
          title="Save Feedback"
          description="Download as text file"
          onClick={() => downloadFeedback(feedback)}
        />
        <ActionCard
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          }
          title="Copy to Clipboard"
          description="Share or save elsewhere"
          onClick={() => copyToClipboard(feedback)}
        />
        <ActionCard
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          }
          title="New Recording"
          description="Analyze another track"
          onClick={onReset}
        />
      </div>
    </div>
  )
}

function FormattedFeedback({ text }) {
  if (!text) return <p className="text-slate-400">No feedback available.</p>
  
  // Simple markdown-like formatting
  const lines = text.split('\n')
  
  return (
    <div className="space-y-2">
      {lines.map((line, i) => {
        // Headers
        if (line.startsWith('### ')) {
          return <h3 key={i} className="text-slate-300 font-medium mt-4">{line.slice(4)}</h3>
        }
        if (line.startsWith('## ')) {
          return <h2 key={i} className="text-coral-400 font-semibold mt-6">{line.slice(3)}</h2>
        }
        if (line.startsWith('# ')) {
          return <h2 key={i} className="text-coral-400 font-bold text-xl mt-6">{line.slice(2)}</h2>
        }
        
        // Bold text with **
        if (line.includes('**')) {
          const parts = line.split(/\*\*(.*?)\*\*/g)
          return (
            <p key={i} className="text-slate-300 leading-relaxed">
              {parts.map((part, j) => 
                j % 2 === 1 ? <strong key={j} className="text-white font-semibold">{part}</strong> : part
              )}
            </p>
          )
        }
        
        // List items
        if (line.startsWith('- ') || line.startsWith('* ')) {
          return (
            <li key={i} className="text-slate-300 ml-4 list-disc">
              {line.slice(2)}
            </li>
          )
        }
        
        // Numbered items
        if (/^\d+\.\s/.test(line)) {
          return (
            <li key={i} className="text-slate-300 ml-4 list-decimal">
              {line.replace(/^\d+\.\s/, '')}
            </li>
          )
        }
        
        // Empty lines
        if (!line.trim()) {
          return <div key={i} className="h-2" />
        }
        
        // Regular paragraph
        return <p key={i} className="text-slate-300 leading-relaxed">{line}</p>
      })}
    </div>
  )
}

function ActionCard({ icon, title, description, onClick }) {
  return (
    <button
      onClick={onClick}
      className="p-4 rounded-xl bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-slate-600 text-left transition-all group"
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-slate-700 group-hover:bg-coral-500/20 flex items-center justify-center text-slate-400 group-hover:text-coral-400 transition-colors">
          {icon}
        </div>
        <div>
          <p className="font-medium text-white">{title}</p>
          <p className="text-xs text-slate-500">{description}</p>
        </div>
      </div>
    </button>
  )
}

function formatAspectName(aspect) {
  const names = {
    pitch: 'Pitch Accuracy',
    timing: 'Timing & Rhythm',
    breath: 'Breath Control',
    expression: 'Expression',
    technique: 'Technique',
    improvements: 'Improvements',
  }
  return names[aspect] || aspect.charAt(0).toUpperCase() + aspect.slice(1)
}

function getAspectIcon(aspect) {
  const icons = {
    pitch: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
      </svg>
    ),
    timing: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    breath: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
      </svg>
    ),
    expression: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    technique: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
    improvements: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    ),
  }
  return icons[aspect] || icons.pitch
}

function downloadFeedback(feedback) {
  let content = `Vocal Critic Analysis\n${'='.repeat(50)}\n\n`
  content += `File: ${feedback.audio_file}\n`
  content += `Type: ${feedback.type}\n`
  content += `Date: ${new Date().toLocaleString()}\n\n`
  
  if (feedback.aspects) {
    for (const [aspect, text] of Object.entries(feedback.aspects)) {
      content += `\n${formatAspectName(aspect)}\n${'-'.repeat(30)}\n${text}\n`
    }
  } else {
    content += feedback.analysis || ''
  }
  
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `vocal-critique-${Date.now()}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

async function copyToClipboard(feedback) {
  let content = ''
  
  if (feedback.aspects) {
    for (const [aspect, text] of Object.entries(feedback.aspects)) {
      content += `## ${formatAspectName(aspect)}\n${text}\n\n`
    }
  } else {
    content = feedback.analysis || ''
  }
  
  try {
    await navigator.clipboard.writeText(content)
    alert('Copied to clipboard!')
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}

