import { ProcessingPanel } from "@/components/ProcessingPanel";
import { Shell } from "@/components/Shell";

export default async function ProcessPage({ params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return (
    <Shell>
      <ProcessingPanel projectId={projectId} />
    </Shell>
  );
}
