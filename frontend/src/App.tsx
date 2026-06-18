import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeContextProvider } from './context/ThemeContext';
import PageLayout from './layouts/PageLayout';
import DashboardPage from './pages/DashboardPage';
import MinePage from './pages/MinePage';
import RequestedPage from './pages/RequestedPage';
import CompletedPage from './pages/CompletedPage';
import SettingsPage from './pages/SettingsPage';

function App() {
  return (
    <ThemeContextProvider>
      <Routes>
        <Route element={<PageLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/mine" element={<MinePage />} />
          <Route path="/requested" element={<RequestedPage />} />
          <Route path="/completed" element={<CompletedPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </ThemeContextProvider>
  );
}

export default App;
