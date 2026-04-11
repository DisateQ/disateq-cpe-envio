/**
 * App.jsx
 * Router principal — une Layout con las 4 páginas
 */

import React, { useState } from 'react'
import Layout       from './components/Layout.jsx'
import Dashboard    from './pages/Dashboard.jsx'
import Comprobantes from './pages/Comprobantes.jsx'
import Log          from './pages/Log.jsx'
import Config       from './pages/Config.jsx'

const PAGES = {
  dashboard:    Dashboard,
  comprobantes: Comprobantes,
  log:          Log,
  config:       Config,
}

export default function App() {
  const [page, setPage] = useState('dashboard')
  const Page = PAGES[page] ?? Dashboard

  return (
    <Layout page={page} onNavigate={setPage}>
      <Page />
    </Layout>
  )
}
