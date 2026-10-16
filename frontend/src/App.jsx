import { useCallback, useEffect, useState } from 'react'
import AudioUploader from './components/AudioUploader'
import FeedbackDisplay from './components/FeedbackDisplay'
import Header from './components/Header'
import LoadingState from './components/LoadingState'

const API_BASE = import.meta.env.DEV ? '/api' : ''

function App() {
  const [file, setFile] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const [feedback, setFeedback] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [group, setGroup] = useState('vocal')
  const [analysisType, setAnalysisType] = useState('comprehensive')
  const [customPrompt, setCustomPrompt] = useState('')
  const [modes, setModes] = useState([])
  const [modelStatus, setModelStatus] = useState({})

  const refreshHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/health`)
      const data = await response.json()
      setModelStatus(data.model_status || {})
    } catch {
      setModelStatus({ status: 'error', error: 'API offline' })
    }
  }, [])

  useEffect(() => {
    refreshHealth()
    const timer = setInterval(refreshHealth, 4000)
    return () => clearInterval(timer)
  }, [refreshHealth])

  useEffect(() => {
    fetch(`${API_BASE}/prompts`)
      .then((res) => res.json())
      .then((data) => setModes(data.modes || []))
      .catch(() => setModes([]))
  }, [])

  const handleFileSelect = useCallback((selectedFile) => {
    setFile(selectedFile)
    setAudioUrl(URL.createObjectURL(selectedFile))
    setFeedback(null)
    setError(null)
  }, [])

  const visibleModes = [
    ...modes.filter((mode) => mode.group === group),
    ...(group === 'music'
      ? [{ id: 'custom', label: 'Ask anything', description: 'Your own question about the recording.' }]
      : []),
  ]

  const handleAnalyze = async () => {
    if (!file) return

    setLoading(true)
    setError(null)
    setFeedback(null)

    try {
      if (analysisType === 'detailed') {
        const formData = new FormData()
        formData.append('file', file)
        const response = await fetch(`${API_BASE}/analyze-sync?analysis_type=detailed`, {
          method: 'POST',
          body: formData,
        })
        if (!response.ok) throw new Error(await readError(response))
        setFeedback(await response.json())
        return
      }

      const formData = new FormData()
      formData.append('file', file)
      const params = new URLSearchParams({ analysis_type: analysisType })
      if (analysisType === 'custom') params.set('prompt', customPrompt)

      const response = await fetch(`${API_BASE}/analyze-stream?${params}`, {
        method: 'POST',
        body: formData,
      })
      if (!response.ok || !response.body) throw new Error(await readError(response))

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let text = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const chunks = buffer.split('\n\n')
        buffer = chunks.pop()
        for (const chunk of chunks) {
          const line = chunk.split('\n').find((item) => item.startsWith('data: '))
          if (!line) continue
          const payload = JSON.parse(line.slice(6))
          if (payload.token) {
            text += payload.token
            setFeedback({
              type: analysisType,
              analysis: text,
              audio_file: file.name,
              streaming: true,
            })
          } else if (payload.analysis) {
            text = payload.analysis
            setFeedback({
              type: analysisType,
              analysis: text,
              audio_file: file.name,
            })
          } else if (payload.error) {
            throw new Error(payload.error)
          }
        }
      }

      if (!text) throw new Error('The model returned an empty response.')
      setFeedback({
        type: analysisType,
        analysis: text,
        audio_file: file.name,
      })
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
      <Header modelStatus={modelStatus} />

      <main className="container mx-auto px-4 py-8 max-w-5xl">
        {!file && (
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-coral-400 to-coral-600 bg-clip-text text-transparent">
              Listen locally. Coach locally.
            </h1>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto">
              Upload a vocal take or a full track. NVIDIA Music Flamingo runs on this
              machine — no Modal, no cloud model.
            </p>
          </div>
        )}

        {!file && <AudioUploader onFileSelect={handleFileSelect} />}

        {file && !feedback && (
          <div className="space-y-6">
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
                  disabled={loading}
                >
                  New file
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

            {!loading && (
              <div className="glass-card rounded-2xl p-6">
                <div className="flex gap-2 mb-5">
                  {[
                    { id: 'vocal', label: 'Vocal coach' },
                    { id: 'music', label: 'Music Flamingo' },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => {
                        setGroup(tab.id)
                        setAnalysisType(tab.id === 'vocal' ? 'comprehensive' : 'describe')
                      }}
                      className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                        group === tab.id
                          ? 'bg-coral-500/15 text-white border border-coral-500'
                          : 'bg-slate-900 text-slate-300 border border-slate-700 hover:border-slate-500'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                <h3 className="text-lg font-medium text-white mb-4">What should it do?</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {visibleModes.map((mode) => (
                    <button
                      key={mode.id}
                      onClick={() => setAnalysisType(mode.id)}
                      className={`p-4 rounded-xl border-2 text-left transition-all ${
                        analysisType === mode.id
                          ? 'border-coral-500 bg-coral-500/10'
                          : 'border-slate-700 hover:border-slate-600'
                      }`}
                    >
                      <span className="block font-medium text-white mb-1">{mode.label}</span>
                      <span className="text-sm text-slate-400">{mode.description}</span>
                    </button>
                  ))}
                </div>

                {analysisType === 'custom' && (
                  <textarea
                    className="mt-4 w-full min-h-[110px] rounded-xl border border-slate-700 bg-slate-950 text-white p-3"
                    placeholder="Ask anything about the track — harmony, lyrics, production, culture…"
                    value={customPrompt}
                    onChange={(event) => setCustomPrompt(event.target.value)}
                  />
                )}
              </div>
            )}

            {!loading && (
              <button
                onClick={handleAnalyze}
                disabled={modelStatus.status === 'loading'}
                className="w-full py-4 px-6 rounded-xl bg-gradient-to-r from-coral-500 to-coral-600 text-white font-semibold text-lg shadow-lg shadow-coral-500/25 hover:shadow-coral-500/40 hover:scale-[1.02] transition-all disabled:opacity-60 disabled:hover:scale-100"
              >
                {modelStatus.status === 'loading' ? 'Waiting for GPU load…' : 'Analyze on the local GPU'}
              </button>
            )}

            {error && (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400">
                {error}
              </div>
            )}
          </div>
        )}

        {loading && !feedback && <LoadingState />}

        {feedback && (
          <FeedbackDisplay
            feedback={feedback}
            audioUrl={audioUrl}
            onReset={handleReset}
          />
        )}
      </main>

      <footer className="py-8 text-center text-slate-500 text-sm">
        <p>Powered by NVIDIA Music Flamingo · research / non-commercial use only · no cloud inference</p>
      </footer>
    </div>
  )
}

async function readError(res) {
  try {
    const data = await res.json()
    return data.detail || JSON.stringify(data)
  } catch {
    return res.statusText
  }
}

export default App
