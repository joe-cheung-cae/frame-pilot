from contextlib import ExitStack
from pathlib import Path

from app.devtools.performance_smoke import (
    PerformanceSmokeConfig,
    PerformanceSmokeSuiteConfig,
    _aggregate_import_timing,
    _list_all_pages,
    _upload_files,
    run_performance_smoke,
    run_performance_smoke_suite,
)


class FakePagedResponse:
    def __init__(self, records: list[dict]):
        self.records = records

    def raise_for_status(self) -> None:
        return None

    def json(self) -> list[dict]:
        return self.records


class FakePagedClient:
    def __init__(self, records: list[dict]):
        self.records = records
        self.requests: list[tuple[str, dict]] = []

    def get(self, path: str, params: dict) -> FakePagedResponse:
        self.requests.append((path, params))
        offset = params["offset"]
        limit = params["limit"]
        return FakePagedResponse(self.records[offset : offset + limit])


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
    assert result["timings"]["import_derivative_seconds"] >= 0
    assert result["timings"]["process_seconds"] >= 0
    assert result["timings"]["export_seconds"] >= 0
    assert result["import_timing"]["batch_count"] == 2
    assert result["import_timing"]["imported_files"] == 3
    assert result["import_timing"]["stages"]["file_copy"]["calls"] == 3
    assert result["import_timing"]["stages"]["content_hash"]["calls"] == 3
    assert result["import_timing"]["slowest_stages"]


def test_performance_smoke_upload_files_use_open_file_handles(tmp_path):
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    first.write_bytes(b"first")
    second.write_bytes(b"second")

    with ExitStack() as stack:
        files = _upload_files([first, second], stack)

        assert [field for field, _payload in files] == ["files", "files"]
        assert [payload[0] for _field, payload in files] == ["first.jpg", "second.jpg"]
        assert all(hasattr(payload[1], "read") for _field, payload in files)
        assert not any(isinstance(payload[1], bytes) for _field, payload in files)


def test_performance_smoke_lists_records_in_pages():
    records = [{"id": f"item-{index}"} for index in range(5)]
    client = FakePagedClient(records)

    assert _list_all_pages(client, "/items", page_size=2) == records
    assert client.requests == [
        ("/items", {"limit": 2, "offset": 0}),
        ("/items", {"limit": 2, "offset": 2}),
        ("/items", {"limit": 2, "offset": 4}),
    ]


def test_performance_smoke_aggregates_import_timing_batches():
    result = _aggregate_import_timing(
        [
            {
                "total_files": 2,
                "imported_files": 2,
                "skipped_files": 0,
                "total_seconds": 1.25,
                "stages": {
                    "preview_generation": {"calls": 2, "seconds": 0.8},
                    "thumbnail_generation": {"calls": 2, "seconds": 0.2},
                    "import_file_total": {"calls": 2, "seconds": 1.0},
                },
            },
            {
                "total_files": 1,
                "imported_files": 1,
                "skipped_files": 0,
                "total_seconds": 0.75,
                "stages": {
                    "preview_generation": {"calls": 1, "seconds": 0.4},
                    "content_hash": {"calls": 1, "seconds": 0.1},
                    "import_endpoint_total": {"calls": 1, "seconds": 0.75},
                },
            },
        ]
    )

    assert result["batch_count"] == 2
    assert result["total_files"] == 3
    assert result["imported_files"] == 3
    assert result["total_seconds"] == 2.0
    assert result["stages"]["preview_generation"] == {
        "calls": 3,
        "seconds": 1.2,
        "seconds_per_imported_file": 0.4,
    }
    assert result["slowest_stages"][0]["stage"] == "preview_generation"
    assert "import_file_total" not in {stage["stage"] for stage in result["slowest_stages"]}
    assert "import_endpoint_total" not in {stage["stage"] for stage in result["slowest_stages"]}


def test_performance_smoke_rejects_invalid_page_size():
    try:
        _list_all_pages(FakePagedClient([]), "/items", page_size=0)
    except ValueError as error:
        assert "page_size" in str(error)
    else:
        raise AssertionError("Expected invalid page size to be rejected")


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
