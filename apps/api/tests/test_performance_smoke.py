from pathlib import Path

from app.devtools.performance_smoke import (
    PerformanceSmokeConfig,
    PerformanceSmokeSuiteConfig,
    run_performance_smoke,
    run_performance_smoke_suite,
)


def test_performance_smoke_reports_local_workflow_metrics(tmp_path):
    result = run_performance_smoke(
        PerformanceSmokeConfig(output_dir=tmp_path, count=3, width=64, height=48, import_batch_size=2)
    )

    assert result["count"] == 3
    assert set(result["exports"]) == {"csv", "folder", "zip"}
    assert result["exports"]["csv"]["bytes"] > 0
    assert result["exports"]["folder"]["file_count"] == 3
    assert result["exports"]["zip"]["bytes"] > 0
    assert all(export["selected_count"] == 3 for export in result["exports"].values())
    assert result["failed_items"] == 0
    assert result["imported_count"] == 3
    assert result["max_rss_mb"] > 0
    assert result["processed_images"] == 3
    assert result["status"] == "complete"
    assert result["timings"]["generate_seconds"] >= 0
    assert result["timings"]["import_seconds"] >= 0
    assert result["timings"]["process_seconds"] >= 0
    assert result["timings"]["export_seconds"] >= 0


def test_performance_smoke_suite_reports_multiple_counts(tmp_path):
    result = run_performance_smoke_suite(
        PerformanceSmokeSuiteConfig(
            output_dir=tmp_path,
            counts=(1, 2),
            width=64,
            height=48,
            import_batch_size=1,
            export_modes=("csv",),
        )
    )

    assert result["counts"] == [1, 2]
    assert result["status"] == "complete"
    assert [item["count"] for item in result["results"]] == [1, 2]

    for item in result["results"]:
        assert item["exports"]["csv"]["bytes"] > 0
        assert item["failed_items"] == 0
        assert item["imported_count"] == item["count"]
        assert item["processed_images"] == item["count"]
        assert Path(item["output_dir"]).parent == tmp_path
