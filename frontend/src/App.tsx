import { useState } from 'react'
import './index.css'
import GrantsPage from './pages/GrantsPage'
import Analytics from './components/Analytics'

type Page = 'grants' | 'analytics'

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('grants')


  return (
    <>
      {/* Navigation */}
      <div style={{
        background: '#2c3e50',
        padding: '16px 32px',
        display: 'flex',
        gap: '16px',
        borderBottom: '3px solid #3498db'
      }}>
        <button
          onClick={() => setCurrentPage('grants')}
          style={{
            background: currentPage === 'grants' ? '#3498db' : 'transparent',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 600,
            transition: 'background 0.2s'
          }}
        >
          📋 Grants
        </button>
        <button
          onClick={() => setCurrentPage('analytics')}
          style={{
            background: currentPage === 'analytics' ? '#3498db' : 'transparent',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 600,
            transition: 'background 0.2s'
          }}
        >
          📊 Analytics
        </button>
      </div>

      {/* Conditional Page Rendering */}
      {currentPage === 'analytics' ? (
        <Analytics />
      ) : (
        <GrantsPage />
      )}
    </>
  )
}

export default App
