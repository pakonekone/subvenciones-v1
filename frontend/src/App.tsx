import { BrowserRouter, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom'
import './index.css'
import LandingPage from './pages/LandingPage'
import GrantsPage from './pages/GrantsPage'
import GrantDetailPage from './pages/GrantDetailPage'
import OrganizationPage from './pages/OrganizationPage'
import Analytics from './components/Analytics'
import { Button } from './components/ui/button'
import { Home, Building2 } from 'lucide-react'

function Navigation() {
  const location = useLocation()
  const currentPath = location.pathname

  // Don't show navigation on landing page
  if (currentPath === '/') {
    return null
  }

  return (
    <div className="bg-slate-900 px-8 py-4 flex items-center gap-4 border-b-4 border-primary">
      <Link to="/">
        <Button
          variant="ghost"
          size="icon"
          className="text-white hover:bg-slate-800"
          title="Volver al inicio"
        >
          <Home className="h-5 w-5" />
        </Button>
      </Link>

      <div className="h-6 w-px bg-slate-700" />

      <Link to="/grants">
        <Button
          variant={currentPath.startsWith('/grants') ? 'secondary' : 'ghost'}
          className={!currentPath.startsWith('/grants') ? 'text-white hover:bg-slate-800' : ''}
        >
          Subvenciones
        </Button>
      </Link>
      <Link to="/analytics">
        <Button
          variant={currentPath === '/analytics' ? 'secondary' : 'ghost'}
          className={currentPath !== '/analytics' ? 'text-white hover:bg-slate-800' : ''}
        >
          Analytics
        </Button>
      </Link>

      <div className="h-6 w-px bg-slate-700 ml-2" />

      <Link to="/organization">
        <Button
          variant={currentPath === '/organization' ? 'secondary' : 'ghost'}
          className={`gap-2 ${currentPath !== '/organization' ? 'text-white hover:bg-slate-800' : ''}`}
        >
          <Building2 className="h-4 w-4" />
          Mi Organizacion
        </Button>
      </Link>
    </div>
  )
}

function LandingWrapper() {
  const navigate = useNavigate()
  return <LandingPage onEnterApp={() => navigate('/grants')} />
}

function AppContent() {
  return (
    <>
      <Navigation />
      <Routes>
        <Route path="/" element={<LandingWrapper />} />
        <Route path="/grants" element={<GrantsPage />} />
        <Route path="/grants/:id" element={<GrantDetailPage />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/organization" element={<OrganizationPage />} />
      </Routes>
    </>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}

export default App
