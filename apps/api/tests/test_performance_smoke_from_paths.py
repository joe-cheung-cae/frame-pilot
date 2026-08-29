from __future__ import annotations

from pathlib import Path

from app.devtools.performance_smoke import PerformanceSmokeConfig, run_performance_smoke


def test_performance_smoke_from_paths_imports_without_mutating_sources(tmp_path: Path) -> None:
    output_dir = tmp_path / "perf-from-paths"
    result = run_performance_smoke(
        PerformanceSmokeConfig(
            output_dir=output_dir,
            count=3,
            import_mode="from-paths",
            export_modes=("csv",),
        )
    )
    assert result["status"] == "complete"
    assert result["import_mode"] == "from-paths"
    assert result["imported_count"] == 3
    assert result["processed_images"] == 3
    sources = sorted((output_dir / "source").glob("*.jpg"))
    assert len(sources) == 3
    for path in sources:
        assert path.stat().st_size > 0
