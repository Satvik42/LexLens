import { useEffect } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import Disclaimer from './components/layout/Disclaimer';
import RequireAuth from './components/layout/RequireAuth';
import { useAuthStore } from './state/authStore';
import Landing from './pages/Landing';
import SignIn from './pages/SignIn';
import Upload from './pages/Upload';
import Documents from './pages/Documents';
import DocumentReady from './pages/DocumentReady';
import Intents from './pages/Intents';
import Analysis from './pages/Analysis';
import AskDocument from './pages/AskDocument';
import LawyerPrep from './pages/LawyerPrep';
import Compare from './pages/Compare';
import Viewer from './pages/Viewer';
import NotFound from './pages/NotFound';

function ScrollToHash() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (hash) {
      const id = hash.slice(1);
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    window.scrollTo(0, 0);
  }, [pathname, hash]);
  return null;
}

function MarketingLayout({ children }) {
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Navbar variant="landing" />
      <main id="main">{children}</main>
      <footer className="site-footer">
        <div className="container">
          <Disclaimer />
        </div>
      </footer>
    </div>
  );
}

function AppLayout({ children }) {
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Navbar variant="app" />
      <main id="main">{children}</main>
      <footer className="site-footer">
        <div className="container">
          <Disclaimer />
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  const initialize = useAuthStore((state) => state.initialize);
  const status = useAuthStore((state) => state.status);

  useEffect(() => {
    let unsubscribe = () => {};
    initialize().then((fn) => {
      if (typeof fn === 'function') unsubscribe = fn;
    });
    return () => unsubscribe();
  }, [initialize]);

  if (status === 'loading') {
    return (
      <div className="app-boot" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" />
        <span>Loading LexLens…</span>
      </div>
    );
  }

  return (
    <>
      <ScrollToHash />
      <Routes>
        <Route
          path="/"
          element={
            <div className="app-shell">
              <a className="skip-link" href="#main">
                Skip to content
              </a>
              <main id="main">
                <Landing />
              </main>
            </div>
          }
        />
        <Route
          path="/signin"
          element={
            <MarketingLayout>
              <SignIn />
            </MarketingLayout>
          }
        />
        <Route
          path="/upload"
          element={
            <AppLayout>
              <RequireAuth>
                <Upload />
              </RequireAuth>
            </AppLayout>
          }
        />
        <Route
          path="/documents"
          element={
            <AppLayout>
              <RequireAuth>
                <Documents />
              </RequireAuth>
            </AppLayout>
          }
        />
        <Route
          path="/documents/:documentId"
          element={
            <AppLayout>
              <RequireAuth>
                <DocumentReady />
              </RequireAuth>
            </AppLayout>
          }
        />
        <Route
          path="/documents/:documentId/intents"
          element={
            <AppLayout>
              <RequireAuth>
                <Intents />
              </RequireAuth>
            </AppLayout>
          }
        />
        <Route
          path="/documents/:documentId/analyze/:operation"
          element={
            <AppLayout>
              <RequireAuth>
                <Analysis />
              </RequireAuth>
            </AppLayout>
          }
        />
        <Route
          path="/documents/:documentId/ask"
          element={
            <AppLayout>
              <RequireAuth>
                <AskDocument />
              </RequireAuth>
            </AppLayout>
          }
        />
        <Route
          path="/documents/:documentId/lawyer"
          element={
            <AppLayout>
              <RequireAuth>
                <LawyerPrep />
              </RequireAuth>
            </AppLayout>
          }
        />
        <Route
          path="/documents/:documentId/compare"
          element={
            <AppLayout>
              <RequireAuth>
                <Compare />
              </RequireAuth>
            </AppLayout>
          }
        />
        <Route
          path="/documents/:documentId/view"
          element={
            <AppLayout>
              <RequireAuth>
                <Viewer />
              </RequireAuth>
            </AppLayout>
          }
        />
        <Route path="/analyze" element={<Navigate to="/upload" replace />} />
        <Route
          path="*"
          element={
            <AppLayout>
              <NotFound />
            </AppLayout>
          }
        />
      </Routes>
    </>
  );
}
