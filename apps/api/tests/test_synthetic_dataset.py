from PIL import Image

from app.devtools.synthetic_dataset import SyntheticDatasetConfig, generate_synthetic_dataset


def test_generate_synthetic_dataset_writes_deterministic_images(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    first_paths = generate_synthetic_dataset(SyntheticDatasetConfig(output_dir=first_dir, count=3, width=64, height=48))
    second_paths = generate_synthetic_dataset(
        SyntheticDatasetConfig(output_dir=second_dir, count=3, width=64, height=48)
    )

    assert [path.name for path in first_paths] == ["frame_000001.jpg", "frame_000002.jpg", "frame_000003.jpg"]
    assert [path.read_bytes() for path in first_paths] == [path.read_bytes() for path in second_paths]
    with Image.open(first_paths[0]) as image:
        assert image.size == (64, 48)
        assert image.format == "JPEG"


def test_generate_synthetic_dataset_supports_png(tmp_path):
    paths = generate_synthetic_dataset(
        SyntheticDatasetConfig(output_dir=tmp_path, count=1, width=64, height=48, image_format="png")
    )

    assert paths[0].name == "frame_000001.png"
    with Image.open(paths[0]) as image:
        assert image.format == "PNG"


def test_generate_synthetic_dataset_accepts_jpeg_quality(tmp_path):
    low_quality_paths = generate_synthetic_dataset(
        SyntheticDatasetConfig(output_dir=tmp_path / "low", count=1, width=160, height=120, jpeg_quality=35)
    )
    high_quality_paths = generate_synthetic_dataset(
        SyntheticDatasetConfig(output_dir=tmp_path / "high", count=1, width=160, height=120, jpeg_quality=95)
    )

    assert low_quality_paths[0].stat().st_size != high_quality_paths[0].stat().st_size


def test_generate_synthetic_dataset_rejects_invalid_count(tmp_path):
    try:
        generate_synthetic_dataset(SyntheticDatasetConfig(output_dir=tmp_path, count=0))
    except ValueError as error:
        assert "count" in str(error)
    else:
        raise AssertionError("Expected invalid count to be rejected")


def test_generate_synthetic_dataset_rejects_invalid_jpeg_quality(tmp_path):
    try:
        generate_synthetic_dataset(SyntheticDatasetConfig(output_dir=tmp_path, count=1, jpeg_quality=101))
    except ValueError as error:
        assert "jpeg_quality" in str(error)
    else:
        raise AssertionError("Expected invalid JPEG quality to be rejected")
