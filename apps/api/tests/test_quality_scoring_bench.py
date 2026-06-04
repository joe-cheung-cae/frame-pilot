from app.devtools.quality_scoring_bench import QualityScoringBenchConfig, run_quality_scoring_bench


def test_quality_scoring_bench_reports_timings_and_score_diffs(tmp_path):
    result = run_quality_scoring_bench(
        QualityScoringBenchConfig(output_dir=tmp_path, count=2, width=64, height=48, jpeg_quality=88)
    )

    assert result["config"] == {"count": 2, "width": 64, "height": 48, "jpeg_quality": 88}
    assert result["timings"]["seconds_per_image"] >= 0
    assert set(result["timings"]["stages"]) == {
        "scoring_image_array",
        "luminance_conversion",
        "sharpness_blur",
        "exposure_contrast_noise",
        "face_signals",
    }
    assert result["score_diff_vs_legacy_full_resolution"]["count"] == 2
    assert result["score_diff_vs_legacy_full_resolution"]["numeric_fields"]["overall_score"]["max_abs_delta"] >= 0.0
    assert len(result["sample_scores"]) == 2
