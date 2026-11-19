import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './Layout'
import { ModuleTracker } from './audit/ModuleTracker'
import { RequireAuth, RequirePerm } from './auth/guards'
import { useAuth } from './auth/AuthProvider'
import { MODULES } from './lib/labels'
import { Login } from './pages/Login'
import { ChangePassword } from './pages/ChangePassword'
import { Forbidden, NotFound } from './pages/Forbidden'
import { SkeletonRows } from './ui/State'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Logs = lazy(() => import('./pages/Logs'))
const Findings = lazy(() => import('./pages/Findings'))
const FindingDetail = lazy(() => import('./pages/FindingDetail'))
const Alerts = lazy(() => import('./pages/Alerts'))
const Reports = lazy(() => import('./pages/Reports'))
const Ingestion = lazy(() => import('./pages/Ingestion'))
const Assets = lazy(() => import('./pages/Assets'))
const Sources = lazy(() => import('./pages/Sources'))
const Lists = lazy(() => import('./pages/Lists'))
const Detection = lazy(() => import('./pages/Detection'))
const Llm = lazy(() => import('./pages/Llm'))
const Users = lazy(() => import('./pages/Users'))
const Roles = lazy(() => import('./pages/Roles'))
const Audit = lazy(() => import('./pages/Audit'))
const MlData = lazy(() => import('./pages/MlData'))
const MlTraining = lazy(() => import('./pages/MlTraining'))
const MlEvaluation = lazy(() => import('./pages/MlEvaluation'))
const MlExplain = lazy(() => import('./pages/MlExplain'))
const MlInference = lazy(() => import('./pages/MlInference'))
const MlOptuna = lazy(() => import('./pages/MlOptuna'))
const Profile = lazy(() => import('./pages/Profile'))

function Home() {
  const { can } = useAuth()
  const first = Object.keys(MODULES).find((m) => can(`${m}:view`))
  return first ? <Navigate to={MODULES[first].path} replace /> : <Forbidden />
}

const guard = (m: string, el: React.ReactNode) => <RequirePerm perm={`${m}:view`}>{el}</RequirePerm>

export default function App() {
  return (
    <>
      <ModuleTracker />
      <Suspense fallback={<div className="page"><SkeletonRows rows={8} /></div>}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/change-password" element={<RequireAuth><ChangePassword /></RequireAuth>} />
          <Route element={<RequireAuth><Layout /></RequireAuth>}>
            <Route index element={<Home />} />
            <Route path="dashboard" element={guard('dashboard', <Dashboard />)} />
            <Route path="logs" element={guard('logs', <Logs />)} />
            <Route path="findings" element={guard('findings', <Findings />)} />
            <Route path="findings/:id" element={guard('findings', <FindingDetail />)} />
            <Route path="alerts" element={guard('alerts', <Alerts />)} />
            <Route path="reports" element={guard('reports', <Reports />)} />
            <Route path="ingestion" element={guard('ingestion', <Ingestion />)} />
            <Route path="assets" element={guard('assets', <Assets />)} />
            <Route path="sources" element={guard('sources', <Sources />)} />
            <Route path="lists" element={guard('lists', <Lists />)} />
            <Route path="detection" element={guard('detection', <Detection />)} />
            <Route path="llm" element={guard('llm', <Llm />)} />
            <Route path="users" element={guard('users', <Users />)} />
            <Route path="roles" element={guard('roles', <Roles />)} />
            <Route path="audit" element={guard('audit', <Audit />)} />
            <Route path="ml/datos" element={guard('ml_data', <MlData />)} />
            <Route path="ml/entrenamiento" element={guard('ml_training', <MlTraining />)} />
            <Route path="ml/evaluacion" element={guard('ml_evaluation', <MlEvaluation />)} />
            <Route path="ml/explicabilidad" element={guard('ml_explain', <MlExplain />)} />
            <Route path="ml/inferencia" element={guard('ml_inference', <MlInference />)} />
            <Route path="ml/optuna" element={guard('ml_optuna', <MlOptuna />)} />
            <Route path="profile" element={<Profile />} />
            <Route path="403" element={<Forbidden />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </Suspense>
    </>
  )
}
