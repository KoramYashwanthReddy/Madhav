import React from 'react';
import { MobileAppProvider, useMobileApp } from './context/MobileAppContext';
import { MobileHeader } from './components/MobileHeader';
import { BottomNavigation } from './components/BottomNavigation';
import { MoreDrawerModal } from './components/MoreDrawerModal';
import { ApprovalModal } from './components/ApprovalModal';
import { EmergencyStopButton } from './components/EmergencyStopButton';

import { HomeView } from './views/HomeView';
import { ChatView } from './views/ChatView';
import { VoiceView } from './views/VoiceView';
import { TasksView } from './views/TasksView';
import { AutomationsView } from './views/AutomationsView';
import { MemoryView } from './views/MemoryView';
import { KnowledgeView } from './views/KnowledgeView';
import { NotificationsView } from './views/NotificationsView';
import { ActivityView } from './views/ActivityView';
import { IntegrationsView } from './views/IntegrationsView';
import { ProfileView } from './views/ProfileView';
import { SettingsView } from './views/SettingsView';
import { DeviceView } from './views/DeviceView';
import { HelpView } from './views/HelpView';

const MainLayout: React.FC = () => {
  const { currentView } = useMobileApp();

  const renderCurrentView = () => {
    switch (currentView) {
      case 'home':
        return <HomeView />;
      case 'chat':
        return <ChatView />;
      case 'voice':
        return <VoiceView />;
      case 'tasks':
        return <TasksView />;
      case 'automations':
        return <AutomationsView />;
      case 'memory':
        return <MemoryView />;
      case 'knowledge':
        return <KnowledgeView />;
      case 'notifications':
        return <NotificationsView />;
      case 'activity':
        return <ActivityView />;
      case 'integrations':
        return <IntegrationsView />;
      case 'profile':
        return <ProfileView />;
      case 'settings':
        return <SettingsView />;
      case 'device':
        return <DeviceView />;
      case 'help':
        return <HelpView />;
      default:
        return <HomeView />;
    }
  };

  return (
    <div className="mobile-app-container">
      <MobileHeader />
      <EmergencyStopButton />
      <main style={{ flex: 1, height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {renderCurrentView()}
      </main>
      <BottomNavigation />
      <MoreDrawerModal />
      <ApprovalModal />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <MobileAppProvider>
      <MainLayout />
    </MobileAppProvider>
  );
};

export default App;
