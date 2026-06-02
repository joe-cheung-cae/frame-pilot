import { ProjectCreator } from "@/components/ProjectCreator";
import { Shell } from "@/components/Shell";

export default function NewProjectPage() {
  return (
    <Shell>
      <section className="mx-auto grid max-w-2xl gap-6 px-5 py-10">
        <div>
          <p className="text-sm text-neutral-600">Local project database</p>
          <h1 className="mt-1 text-3xl font-semibold">Create Project</h1>
        </div>
        <div className="rounded border border-line bg-white p-5">
          <ProjectCreator />
        </div>
      </section>
    </Shell>
  );
}

