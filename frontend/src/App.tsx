import { Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import ProjectExplorer from './pages/ProjectExplorer';
import { Toaster } from './components/ui/toaster';

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/project/:collection" element={<ProjectExplorer />} />
      </Routes>
      <Toaster />
    </>
  );
}

export default App;