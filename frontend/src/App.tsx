import { DashboardProvider } from '@/context/DashboardContext';
import { Dashboard } from '@/components/dashboard/Dashboard';

export default function App() {
  return (
    <DashboardProvider>
      <Dashboard />
    </DashboardProvider>
  );
}