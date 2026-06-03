import { Shell } from "@/components/Shell";
import { REVIEW_SHORTCUT_HELP_SECTIONS } from "@/lib/reviewShortcuts";

export default function HelpPage() {
  return (
    <Shell>
      <section className="mx-auto grid max-w-5xl gap-8 px-5 py-10">
        <div className="grid gap-2">
          <p className="text-sm text-neutral-600">Review reference</p>
          <h1 className="text-3xl font-semibold">Keyboard Shortcuts</h1>
          <p className="max-w-2xl text-neutral-700">
            These shortcuts work in the culling workspace after a project has imported and processed photos.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {REVIEW_SHORTCUT_HELP_SECTIONS.map((section) => (
            <section key={section.title} className="rounded border border-line bg-white p-5">
              <h2 className="text-sm font-semibold text-neutral-600">{section.title}</h2>
              <dl className="mt-4 grid gap-3">
                {section.shortcuts.map((shortcut) => (
                  <div key={shortcut.keys} className="grid grid-cols-[7rem_1fr] items-center gap-3">
                    <dt>
                      <kbd className="inline-flex min-h-8 min-w-8 items-center justify-center rounded border border-line bg-mist px-2 text-sm font-semibold text-ink">
                        {shortcut.keys}
                      </kbd>
                    </dt>
                    <dd className="text-sm text-neutral-700">{shortcut.action}</dd>
                  </div>
                ))}
              </dl>
            </section>
          ))}
        </div>
      </section>
    </Shell>
  );
}
