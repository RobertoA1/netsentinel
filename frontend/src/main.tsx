import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App'
import { AuthProvider } from './auth/AuthProvider'
import { ThemeProvider } from './lib/theme'
import { ToastProvider } from './ui/Toast'
import { ApiError, setFetchImpl } from './api/client'

const qc = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15_000, refetchOnWindowFocus: false,
      retry: (n, e) => !(e instanceof ApiError && e.status < 500) && n < 2,
    },
  },
})

async function boot() {
  // El modo mock existe solo en desarrollo: en producción esta rama se elimina del bundle.
  if (import.meta.env.DEV && import.meta.env.VITE_MOCK === '1') {
    const { mockFetch } = await import('./mock/handler')
    setFetchImpl(mockFetch)
  }
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <QueryClientProvider client={qc}>
        <ThemeProvider>
          <BrowserRouter>
            <ToastProvider>
              <AuthProvider>
                <App />
              </AuthProvider>
            </ToastProvider>
          </BrowserRouter>
        </ThemeProvider>
      </QueryClientProvider>
    </StrictMode>,
  )
}
void boot()
