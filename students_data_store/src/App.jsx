import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './router/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import RouteErrorBoundary from './components/RouteErrorBoundary';

// Eagerly load only public/authentication routes
import Login from './pages/Login';
import NotAuthorized from './pages/NotAuthorized';
import ShareStudentForm from './pages/ShareStudentForm';

// Lazy-load all admin pages — they are only loaded when the user navigates there
const Dashboard   = lazy(() => import('./pages/Dashboard'));
const UsersPage   = lazy(() => import('./pages/UsersPage'));
const RolesPage   = lazy(() => import('./pages/RolesPage'));
const StudentsPage = lazy(() => import('./pages/StudentsPage'));
const StudentReport = lazy(() => import('./pages/StudentReport'));
const EmailHistoryPage = lazy(() => import('./pages/EmailHistoryPage'));

// Lightweight spinner shown while a lazy page chunk is loading
function PageLoader() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-gray-50">
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin" />
        <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Loading...</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Public routes — always bundled, no loading delay */}
            <Route path="/login"         element={<Login />} />
            <Route path="/not-authorized" element={<NotAuthorized />} />
            <Route
              path="/form/:token"
              element={
                <RouteErrorBoundary routeName="Student Form">
                  <ShareStudentForm />
                </RouteErrorBoundary>
              }
            />

            {/* Protected routes — lazy loaded with error boundaries */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <RouteErrorBoundary routeName="Dashboard">
                    <Dashboard />
                  </RouteErrorBoundary>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute permission="admin:manage_users">
                  <RouteErrorBoundary routeName="Users Management">
                    <UsersPage />
                  </RouteErrorBoundary>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/roles"
              element={
                <ProtectedRoute permission="admin:manage_roles">
                  <RouteErrorBoundary routeName="Roles Management">
                    <RolesPage />
                  </RouteErrorBoundary>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/students"
              element={
                <ProtectedRoute permission="students:read">
                  <RouteErrorBoundary routeName="Students Management">
                    <StudentsPage />
                  </RouteErrorBoundary>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/students/report"
              element={
                <ProtectedRoute permission="students:read">
                  <RouteErrorBoundary routeName="Student Report">
                    <StudentReport />
                  </RouteErrorBoundary>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/emails"
              element={
                <ProtectedRoute permission="admin:manage_users">
                  <RouteErrorBoundary routeName="Email History">
                    <EmailHistoryPage />
                  </RouteErrorBoundary>
                </ProtectedRoute>
              }
            />

            {/* Default redirect */}
            <Route path="/"  element={<Navigate to="/dashboard" replace />} />
            <Route path="*"  element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
