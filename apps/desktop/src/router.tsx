import type { ReactNode } from "react";
import { Navigate, Route, Routes, useParams } from "react-router-dom";
import { CullingWorkspace } from "@/components/CullingWorkspace";
import { ExportPanel } from "@/components/ExportPanel";
import { HelpShortcuts } from "@/components/HelpShortcuts";
import { ImportPanel } from "@/components/ImportPanel";
import { ProcessingPanel } from "@/components/ProcessingPanel";
import { ProjectCreator } from "@/components/ProjectCreator";
import { ProjectDashboard } from "@/components/ProjectDashboard";
import { ProjectList } from "@/components/ProjectList";
import { SettingsPanel } from "@/components/SettingsPanel";
import { Shell } from "@/components/Shell";

function HomePage() {
  return (
    <Shell>
      <section className="mx-auto max-w-7xl px-5 py-8">
        <div className="rounded border border-line bg-surface p-5">
          <h2 className="mb-4 font-semibold">Recent Projects</h2>
          <ProjectList />
        </div>
      </section>
    </Shell>
  );
}

function HelpPage() {
  return (
    <Shell>
      <HelpShortcuts />
    </Shell>
  );
}

function SettingsPage() {
  return (
    <Shell>
      <SettingsPanel />
    </Shell>
  );
}

function NewProjectPage() {
  return (
    <Shell>
      <section className="mx-auto grid max-w-2xl gap-6 px-5 py-10">
        <div>
          <p className="text-sm text-muted">Local project database</p>
          <h1 className="mt-1 text-3xl font-semibold">Create Project</h1>
        </div>
        <div className="rounded border border-line bg-surface p-5">
          <ProjectCreator />
        </div>
      </section>
    </Shell>
  );
}

function ProjectIdPage({ children }: { children: (projectId: string) => ReactNode }) {
  const { projectId } = useParams<{ projectId: string }>();
  if (!projectId) {
    return <Navigate to="/" replace />;
  }
  return <Shell>{children(projectId)}</Shell>;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/help" element={<HelpPage />} />
      <Route path="/settings" element={<SettingsPage />} />
      <Route path="/projects/new" element={<NewProjectPage />} />
      <Route
        path="/projects/:projectId"
        element={<ProjectIdPage>{(projectId) => <ProjectDashboard projectId={projectId} />}</ProjectIdPage>}
      />
      <Route
        path="/projects/:projectId/import"
        element={<ProjectIdPage>{(projectId) => <ImportPanel projectId={projectId} />}</ProjectIdPage>}
      />
      <Route
        path="/projects/:projectId/process"
        element={<ProjectIdPage>{(projectId) => <ProcessingPanel projectId={projectId} />}</ProjectIdPage>}
      />
      <Route
        path="/projects/:projectId/cull"
        element={<ProjectIdPage>{(projectId) => <CullingWorkspace projectId={projectId} />}</ProjectIdPage>}
      />
      <Route
        path="/projects/:projectId/export"
        element={<ProjectIdPage>{(projectId) => <ExportPanel projectId={projectId} />}</ProjectIdPage>}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
