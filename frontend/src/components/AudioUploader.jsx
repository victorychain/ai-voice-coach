import { useState, useRef, useCallback } from 'react'

const ACCEPTED_FORMATS = '.wav,.mp3,.flac,.m4a,.ogg'

export default function AudioUploader({ onFileSelect }) {
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef(null)

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDragIn = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true)
    }
  }, [])

  const handleDragOut = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0]
      if (isValidAudioFile(file)) {
        onFileSelect(file)
      }
      e.dataTransfer.clearData()
    }
  }, [onFileSelect])

  const handleFileChange = useCallback((e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(e.target.files[0])
    }
  }, [onFileSelect])

  const isValidAudioFile = (file) => {
    const validTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/flac', 'audio/m4a', 'audio/ogg', 'audio/x-m4a']
    return validTypes.includes(file.type) || file.name.match(/\.(wav|mp3|flac|m4a|ogg)$/i)
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div
      onDragEnter={handleDragIn}
      onDragLeave={handleDragOut}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`
        drop-zone relative cursor-pointer
        border-2 border-dashed rounded-2xl p-12
        transition-all duration-300 ease-out
        ${isDragging 
          ? 'active border-coral-500 bg-coral-500/10' 
          : 'border-slate-700 hover:border-slate-500 bg-slate-800/30'
        }
      `}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_FORMATS}
        onChange={handleFileChange}
        className="hidden"
      />

      <div className="flex flex-col items-center gap-6">
        {/* Animated upload icon */}
        <div className={`
          relative w-20 h-20 rounded-2xl 
          bg-gradient-to-br from-coral-500/20 to-coral-600/10
          flex items-center justify-center
          ${isDragging ? 'scale-110' : ''}
          transition-transform duration-300
        `}>
          <svg 
            className={`w-10 h-10 ${isDragging ? 'text-coral-400' : 'text-coral-500'} transition-colors`} 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={1.5} 
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" 
            />
          </svg>
          
          {/* Decorative rings */}
          <div className="absolute inset-0 rounded-2xl border border-coral-500/20 animate-pulse-slow" />
          <div className="absolute -inset-2 rounded-3xl border border-coral-500/10 animate-pulse-slow" style={{ animationDelay: '0.5s' }} />
        </div>

        {/* Text */}
        <div className="text-center">
          <p className="text-lg font-medium text-white mb-2">
            {isDragging ? 'Drop your audio file here' : 'Drag & drop your recording'}
          </p>
          <p className="text-slate-400">
            or <span className="text-coral-400 hover:text-coral-300 underline underline-offset-2">browse files</span>
          </p>
        </div>

        {/* Format info */}
        <div className="flex flex-wrap justify-center gap-2">
          {['WAV', 'MP3', 'FLAC', 'M4A', 'OGG'].map((format) => (
            <span 
              key={format}
              className="px-3 py-1 rounded-full text-xs font-medium bg-slate-700/50 text-slate-400"
            >
              {format}
            </span>
          ))}
        </div>

        <p className="text-xs text-slate-500">
          Maximum file size: 100MB • Up to 20 minutes of audio
        </p>
      </div>
    </div>
  )
}

