import { ImportPanel } from "@/components/ImportPanel";
import { Shell } from "@/components/Shell";

export default async function ImportPage({ params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return (
    <Shell>
      <ImportPanel projectId={projectId} />
    </Shell>
  );
}
