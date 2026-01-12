import { useState } from 'react'
import './index.css'
import LandingPage from './pages/LandingPage'
import GrantsPage from './pages/GrantsPage'
import Analytics from './components/Analytics'
import { Button } from './components/ui/button'
import { Home } from 'lucide-react'

type Page = 'landing' | 'grants' | 'analytics'

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('landing')

  // Show landing page without navigation
  if (currentPage === 'landing') {
    return <LandingPage onEnterApp={() => setCurrentPage('grants')} />
  }

  return (
    <>
      {/* Navigation */}
      <div className="bg-slate-900 px-8 py-4 flex items-center gap-4 border-b-4 border-primary">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCurrentPage('landing')}
          className="text-white hover:bg-slate-800"
          title="Volver al inicio"
        >
          <Home className="h-5 w-5" />
        </Button>

        <div className="h-6 w-px bg-slate-700" />

        <Button
          variant={currentPage === 'grants' ? 'secondary' : 'ghost'}
          onClick={() => setCurrentPage('grants')}
          className={currentPage !== 'grants' ? 'text-white hover:bg-slate-800' : ''}
        >
          Subvenciones
        </Button>
        <Button
          variant={currentPage === 'analytics' ? 'secondary' : 'ghost'}
          onClick={() => setCurrentPage('analytics')}
          className={currentPage !== 'analytics' ? 'text-white hover:bg-slate-800' : ''}
        >
          Analytics
        </Button>
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
