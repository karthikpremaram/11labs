
import axios from 'axios';
import React from 'react';
// eslint-disable-next-line no-unused-vars
import { useRef, useState } from 'react';

export default function App() {
  const [text, setText] = useState('Hello from 11Labs!')
  const [loading, setLoading] = useState(false)
  const audioRef = useRef(null)
  const [blobUrl, setBlobUrl] = useState(null)

  async function handleConvert() {
    setLoading(true)
    try {
      const resp = await axios.post('http://localhost:8000/stream_tts', {
        text,
        audio_name: 'output',
      }, {
        responseType: 'blob'
      })

      const blob = new Blob([resp.data], { type: 'audio/mpeg' })
      if (audioRef.current) {
        audioRef.current.src = URL.createObjectURL(blob)
        await audioRef.current.play()
      }
    } catch (err) {
      console.error(err)
      alert('Conversion failed; check backend logs and API key')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>Text → Speech</h1>
      <textarea value={text} onChange={e => setText(e.target.value)} rows={6} />
      <div className="controls">
        <button onClick={handleConvert} disabled={loading}>
          {loading ? 'Converting...' : 'Convert'}
        </button>
        <audio ref={audioRef} controls />
      </div>
    </div>
  )
}
