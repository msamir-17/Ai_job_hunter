import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { Header } from './components/layout/Header';
import { Home } from './pages/Home';
import { ResumeReviewPage } from './pages/ResumeReviewPage';
import { CandidateProfilePage } from './pages/CandidateProfilePage';
import { JobDiscoveryPage } from './pages/JobDiscoveryPage';
import { ApplicationsKanbanPage } from './pages/ApplicationsKanbanPage';

const queryClient = new QueryClient();

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <div className="min-h-screen bg-[#f7f8fa] text-[#1a1d23] flex flex-col font-sans selection:bg-blue-100 selection:text-blue-800">
            <Header />
            <main className="flex-1">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/profile" element={<CandidateProfilePage />} />
              <Route path="/resume-review" element={<ResumeReviewPage />} />
              <Route path="/jobs" element={<JobDiscoveryPage />} />
              <Route path="/applications" element={<ApplicationsKanbanPage />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  </QueryClientProvider>
);
};

export default App;
