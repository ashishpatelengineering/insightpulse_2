import { Component } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Sidebar from "./components/Sidebar.jsx";
import ModePage from "./components/ModePage.jsx";
import { LogoMark } from "./components/Icons.jsx";
import { MODES } from "./modes/config.js";

class ErrorBoundary extends Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error) {
    console.error(error);
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div className="fatal">
        <h1>Something went wrong</h1>
        <p>The page could not be shown. Please reload and try again.</p>
        <button type="button" className="btn btn-primary" onClick={() => window.location.reload()}>
          Reload page
        </button>
      </div>
    );
  }
}

export default function App() {
  return (
    <div className="app">
      <header className="brand-bar">
        <LogoMark size={26} />
        <span className="brand-name">InsightPulse</span>
      </header>
      <Sidebar />
      <main className="content">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Navigate to={MODES[0].path} replace />} />
            {MODES.map((mode) => (
              <Route key={mode.id} path={mode.path} element={<ModePage key={mode.id} mode={mode} />} />
            ))}
            <Route path="*" element={<Navigate to={MODES[0].path} replace />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  );
}
