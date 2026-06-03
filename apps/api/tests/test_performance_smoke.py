from app.devtools.performance_smoke import PerformanceSmokeConfig, run_performance_smoke


def test_performance_smoke_reports_local_workflow_metrics(tmp_path):
    result = run_performance_smoke(
        PerformanceSmokeConfig(output_dir=tmp_path, count=3, width=64, height=48, import_batch_size=2)
    )

    assert result["count"] == 3
    assert result["failed_items"] == 0
    assert result["imported_count"] == 3
    assert result["max_rss_mb"] > 0
    assert result["processed_images"] == 3
    assert result["status"] == "complete"
    assert result["timings"]["generate_seconds"] >= 0
    assert result["timings"]["import_seconds"] >= 0
    assert result["timings"]["process_seconds"] >= 0
