let meta = #{
    name: "d3-02-status-bar",
    description: "Investigate, plan, implement, and verify FramePilot D3.02 status bar (issue 46)",
    when_to_use: "Land GitHub issue 46 / task D3.02 Status bar on feature/d3-02-status-bar without pushing or opening a PR",
    phases: [
        #{ title: "Investigate", detail: "Read spec, live Shell, processingProgress, health, and desktop shell flag" },
        #{ title: "Plan", detail: "Tests-first D3.02 plan from live evidence" },
        #{ title: "Implement", detail: "Failing tests, desktop status bar, tracker tick, local commit" },
        #{ title: "Verify", detail: "Run named tests, review diff, confirm D3.03+ untouched" },
    ],
};
