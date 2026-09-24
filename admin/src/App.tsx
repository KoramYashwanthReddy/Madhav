import React from 'react';
import { AdminProvider, useAdmin } from './context/AdminContext';
import { AdminHeader } from './components/AdminHeader';
import { AdminSidebar } from './components/AdminSidebar';
import { KillSwitchModal } from './components/KillSwitchModal';
import { DangerousActionModal } from './components/DangerousActionModal';
import { GlobalSearchModal } from './components/GlobalSearchModal';

import { DashboardView } from './views/DashboardView';
import { RuntimeView } from './views/RuntimeView';
import { ModelsView } from './views/ModelsView';
import { AgentsView } from './views/AgentsView';
import { ToolsView } from './views/ToolsView';
import { SecurityView } from './views/SecurityView';
import { TasksView } from './views/TasksView';
import { AutomationsView } from './views/AutomationsView';
import { DevicesView } from './views/DevicesView';
import { IntegrationsView } from './views/IntegrationsView';
import { NotificationsView } from './views/NotificationsView';
import { ObservabilityView } from './views/ObservabilityView';
import { AuditView } from './views/AuditView';
import { EvaluationsView } from './views/EvaluationsView';
import { ConfigurationView } from './views/ConfigurationView';
import { DiagnosticsView } from './views/DiagnosticsView';
import { SettingsView } from './views/SettingsView';

const MainLayout: React.FC = () => {
  const { activeSection } = useAdmin();

  const renderActiveSection = () => {
    switch (activeSection) {
      case 'dashboard':
        return <DashboardView />;
      case 'runtime':
        return <RuntimeView />;
      case 'models':
        return <ModelsView />;
      case 'agents':
        return <AgentsView />;
      case 'tools':
        return <ToolsView />;
      case 'security':
        return <SecurityView />;
      case 'tasks':
        return <TasksView />;
      case 'automations':
        return <AutomationsView />;
      case 'devices':
        return <DevicesView />;
      case 'integrations':
        return <IntegrationsView />;
      case 'notifications':
        return <NotificationsView />;
      case 'observability':
        return <ObservabilityView />;
      case 'audit':
        return <AuditView />;
      case 'evaluations':
        return <EvaluationsView />;
      case 'configuration':
        return <ConfigurationView />;
      case 'diagnostics':
        return <DiagnosticsView />;
      case 'settings':
        return <SettingsView />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="admin-app-container">
      <AdminHeader />
      <div className="admin-main-layout">
        <AdminSidebar />
        <main style={{ flex: 1, height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {renderActiveSection()}
        </main>
      </div>

      <KillSwitchModal />
      <DangerousActionModal />
      <GlobalSearchModal />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AdminProvider>
      <MainLayout />
    </AdminProvider>
  );
};

export default App;
