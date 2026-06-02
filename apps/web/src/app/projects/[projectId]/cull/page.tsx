import { CullingWorkspace } from "@/components/CullingWorkspace";
import { Shell } from "@/components/Shell";

export default async function CullPage({ params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return (
    <Shell>
      <CullingWorkspace projectId={projectId} />
    </Shell>
  );
}
