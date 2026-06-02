import { ProjectList } from "@/components/ProjectList";
import { Shell } from "@/components/Shell";

export default function HomePage() {
  return (
    <Shell>
      <section className="mx-auto grid max-w-7xl gap-8 px-5 py-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="grid content-start gap-5">
          <h1 className="max-w-3xl text-4xl font-semibold leading-tight">Turn large shoots into a clean reviewable shortlist.</h1>
          <p className="max-w-2xl text-neutral-700">
            Create a local project, import images, generate previews, group similar frames, and keep the final culling decision under your control.
          </p>
        </div>
        <div className="rounded border border-line bg-white p-5">
          <h2 className="mb-4 font-semibold">Recent Projects</h2>
          <ProjectList />
        </div>
      </section>
    </Shell>
  );
}

