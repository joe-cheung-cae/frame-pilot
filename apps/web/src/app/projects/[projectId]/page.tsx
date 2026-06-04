import { ProjectDashboard } from "@/components/ProjectDashboard";
import { Shell } from "@/components/Shell";

export default async function ProjectPage({ params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return (
    <Shell>
      <ProjectDashboard projectId={projectId} />
    </Shell>
  );
}
