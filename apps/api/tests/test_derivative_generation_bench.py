from app.devtools.derivative_generation_bench import (
    DerivativeGenerationBenchConfig,
    run_derivative_generation_bench,
)


def test_derivative_generation_bench_reports_timings_and_outputs(tmp_path):
    result = run_derivative_generation_bench(
        DerivativeGenerationBenchConfig(output_dir=tmp_path, count=2, width=64, height=48, jpeg_quality=88)
    )

    assert result["config"] == {"count": 2, "width": 64, "height": 48, "jpeg_quality": 88}
    assert result["preview_settings"] == {"format": "WEBP", "long_edge": 1800, "quality": 88, "method": 2}
    assert result["thumbnail_settings"] == {"format": "WEBP", "long_edge": 320, "quality": 82}
    assert set(result["timings"]["stages"]) == {
        "image_open",
        "image_decode",
        "orientation_handling",
        "rgb_conversion",
        "preview_resize",
        "preview_webp_encode",
        "thumbnail_generation",
        "combined_derivative_generation",
    }
    assert result["timings"]["combined_seconds_per_image"] >= 0
    assert result["outputs"]["preview_bytes"]["min"] > 0
    assert result["outputs"]["combined_preview_bytes"]["min"] > 0
    assert result["outputs"]["preview_dimensions"]["long_edge_bounded"] is True
    assert result["outputs"]["thumbnail_dimensions"]["long_edge_bounded"] is True
