import React, { useState, useEffect } from 'react';
import { AuthUser } from './types';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { SensorsPage } from './pages/SensorsPage';
import { ThresholdsPage } from './pages/ThresholdsPage';
import { ActuatorsPage } from './pages/ActuatorsPage';
import { DevicesPage } from './pages/DevicesPage';
import { AlertsPage } from './pages/AlertsPage';
import { AuditLogsPage } from './pages/AuditLogsPage';
import { api } from './services/api';

export const App: React.FC = () => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [alertCount, setAlertCount] = useState<number>(0);

  useEffect(() => {
    const savedUser = localStorage.getItem('agri_user');
    const token = localStorage.getItem('agri_jwt_token');
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem('agri_user');
        localStorage.removeItem('agri_jwt_token');
      }
    }
  }, []);

  useEffect(() => {
    if (user) {
      api.getAlerts(false)
        .then((data) => setAlertCount(data.length))
        .catch(() => {});
      const interval = setInterval(() => {
        api.getAlerts(false)
          .then((data) => setAlertCount(data.length))
          .catch(() => {});
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const handleLogout = () => {
    localStorage.removeItem('agri_user');
    localStorage.removeItem('agri_jwt_token');
    setUser(null);
  };

  if (!user) {
    return <LoginPage onLoginSuccess={(u) => setUser(u)} />;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar user={user} onLogout={handleLogout} />

      <div className="flex flex-1">
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          userRole={user.role}
          alertCount={alertCount}
        />

        <main className="flex-1 p-8 overflow-y-auto max-w-7xl">
          {currentTab === 'dashboard' && <DashboardPage />}
          {currentTab === 'sensors' && <SensorsPage />}
          {currentTab === 'thresholds' && <ThresholdsPage userRole={user.role} />}
          {currentTab === 'actuators' && <ActuatorsPage userRole={user.role} />}
          {currentTab === 'devices' && <DevicesPage userRole={user.role} />}
          {currentTab === 'alerts' && <AlertsPage userRole={user.role} />}
          {currentTab === 'audit' && <AuditLogsPage userRole={user.role} />}
        </main>
      </div>
    </div>
  );
};

export default App;
