import { ExportPanel } from "@/components/ExportPanel";
import { Shell } from "@/components/Shell";

export default async function ExportPage({ params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return (
    <Shell>
      <ExportPanel projectId={projectId} />
    </Shell>
  );
}
