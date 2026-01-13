import { useState, useCallback } from 'react'
import AudioUploader from './components/AudioUploader'
import FeedbackDisplay from './components/FeedbackDisplay'
import Header from './components/Header'
import LoadingState from './components/LoadingState'

const API_BASE = '/api'

function App() {
  const [file, setFile] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const [feedback, setFeedback] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [analysisType, setAnalysisType] = useState('comprehensive')

  const handleFileSelect = useCallback((selectedFile) => {
    setFile(selectedFile)
    setAudioUrl(URL.createObjectURL(selectedFile))
    setFeedback(null)
    setError(null)
  }, [])

  const handleAnalyze = async () => {
    if (!file) return

    setLoading(true)
    setError(null)
    setFeedback(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${API_BASE}/analyze-sync?analysis_type=${analysisType}`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Analysis failed')
      }

      const result = await response.json()
      setFeedback(result)
    } catch (err) {
      setError(err.message || 'Failed to analyze audio. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setAudioUrl(null)
    setFeedback(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-pattern">
      <Header />
      
      <main className="container mx-auto px-4 py-8 max-w-5xl">
        {/* Hero Section */}
        {!file && (
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-coral-400 to-coral-600 bg-clip-text text-transparent">
              Elevate Your Voice
            </h1>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto">
              Get professional AI-powered feedback on your singing. Upload a recording and receive 
              detailed critiques on pitch, timing, expression, and technique.
            </p>
          </div>
        )}

        {/* Upload Zone */}
        {!file && (
          <AudioUploader onFileSelect={handleFileSelect} />
        )}

        {/* File Selected - Ready to Analyze */}
        {file && !loading && !feedback && (
          <div className="space-y-6">
            {/* Selected File Card */}
            <div className="glass-card rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-coral-500/20 flex items-center justify-center">
                    <svg className="w-6 h-6 text-coral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-white">{file.name}</p>
                    <p className="text-sm text-slate-400">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleReset}
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Audio Player */}
              {audioUrl && (
                <audio 
                  controls 
                  src={audioUrl} 
                  className="w-full h-12 rounded-lg"
                  style={{ filter: 'sepia(20%) saturate(70%) grayscale(1) contrast(99%) invert(12%)' }}
                />
              )}
            </div>

            {/* Analysis Type Selection */}
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-lg font-medium text-white mb-4">Analysis Type</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                  onClick={() => setAnalysisType('comprehensive')}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    analysisType === 'comprehensive'
                      ? 'border-coral-500 bg-coral-500/10'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`w-4 h-4 rounded-full border-2 ${
                      analysisType === 'comprehensive' ? 'border-coral-500 bg-coral-500' : 'border-slate-500'
                    }`} />
                    <span className="font-medium text-white">Comprehensive</span>
                  </div>
                  <p className="text-sm text-slate-400 ml-7">
                    Full analysis covering all aspects in a single detailed report
                  </p>
                </button>
                <button
                  onClick={() => setAnalysisType('detailed')}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    analysisType === 'detailed'
                      ? 'border-coral-500 bg-coral-500/10'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`w-4 h-4 rounded-full border-2 ${
                      analysisType === 'detailed' ? 'border-coral-500 bg-coral-500' : 'border-slate-500'
                    }`} />
                    <span className="font-medium text-white">Detailed</span>
                  </div>
                  <p className="text-sm text-slate-400 ml-7">
                    Separate in-depth analysis for each aspect (pitch, timing, etc.)
                  </p>
                </button>
              </div>
            </div>

            {/* Analyze Button */}
            <button
              onClick={handleAnalyze}
              className="w-full py-4 px-6 rounded-xl bg-gradient-to-r from-coral-500 to-coral-600 text-white font-semibold text-lg shadow-lg shadow-coral-500/25 hover:shadow-coral-500/40 hover:scale-[1.02] transition-all"
            >
              Analyze My Performance
            </button>

            {error && (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400">
                {error}
              </div>
            )}
          </div>
        )}

        {/* Loading State */}
        {loading && <LoadingState />}

        {/* Feedback Display */}
        {feedback && (
          <FeedbackDisplay 
            feedback={feedback} 
            audioUrl={audioUrl}
            onReset={handleReset}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="py-8 text-center text-slate-500 text-sm">
        <p>Powered by Music Flamingo | For research purposes only</p>
      </footer>
    </div>
  )
}

export default App

