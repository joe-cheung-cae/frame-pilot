from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SUPPORTED_FORMATS = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}


@dataclass(frozen=True)
class SyntheticDatasetConfig:
    output_dir: Path
    count: int
    width: int = 160
    height: int = 120
    image_format: str = "jpg"
    burst_size: int = 5


def _validate_config(config: SyntheticDatasetConfig) -> str:
    if config.count <= 0:
        raise ValueError("count must be greater than zero")
    if config.width < 32 or config.height < 32:
        raise ValueError("width and height must be at least 32 pixels")
    if config.burst_size <= 0:
        raise ValueError("burst_size must be greater than zero")

    normalized_format = config.image_format.lower().lstrip(".")
    if normalized_format not in SUPPORTED_FORMATS:
        raise ValueError(f"format must be one of {sorted(SUPPORTED_FORMATS)}")
    return normalized_format


def _base_color(burst_index: int) -> tuple[int, int, int]:
    return (
        70 + (burst_index * 37) % 130,
        80 + (burst_index * 53) % 120,
        90 + (burst_index * 29) % 110,
    )


def _render_frame(index: int, config: SyntheticDatasetConfig) -> Image.Image:
    burst_index = index // config.burst_size
    frame_index = index % config.burst_size
    base = _base_color(burst_index)
    image = Image.new("RGB", (config.width, config.height), base)
    draw = ImageDraw.Draw(image)

    offset = frame_index * 3
    draw.rectangle(
        (
            12 + offset,
            10 + offset,
            max(13 + offset, config.width // 2 + offset),
            max(11 + offset, config.height // 2 + offset),
        ),
        outline=(235, 235, 235),
        width=3,
    )
    draw.ellipse(
        (
            config.width // 2 - 10 + offset,
            config.height // 2 - 8,
            config.width // 2 + 26 + offset,
            config.height // 2 + 28,
        ),
        fill=(min(base[0] + 40, 255), max(base[1] - 20, 0), max(base[2] - 25, 0)),
    )
    draw.line((0, config.height - 1 - offset, config.width, offset), fill=(30, 30, 30), width=2)

    if index % 15 == 13:
        image = Image.blend(image, Image.new("RGB", image.size, (245, 245, 245)), 0.72)
    elif index % 15 == 14:
        image = Image.blend(image, Image.new("RGB", image.size, (8, 8, 8)), 0.72)
    elif index % 10 == 9:
        image = image.filter(ImageFilter.GaussianBlur(radius=3))

    return image


def generate_synthetic_dataset(config: SyntheticDatasetConfig) -> list[Path]:
    normalized_format = _validate_config(config)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    extension = "jpg" if normalized_format == "jpeg" else normalized_format
    paths: list[Path] = []

    for index in range(config.count):
        path = config.output_dir / f"frame_{index + 1:06d}.{extension}"
        image = _render_frame(index, config)
        save_kwargs = {"quality": 88} if SUPPORTED_FORMATS[normalized_format] == "JPEG" else {}
        image.save(path, format=SUPPORTED_FORMATS[normalized_format], **save_kwargs)
        paths.append(path)

    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate deterministic local images for FramePilot performance tests."
    )
    parser.add_argument("--output", required=True, type=Path, help="Directory to write generated images into.")
    parser.add_argument("--count", required=True, type=int, help="Number of images to generate.")
    parser.add_argument("--width", default=160, type=int, help="Generated image width in pixels.")
    parser.add_argument("--height", default=120, type=int, help="Generated image height in pixels.")
    parser.add_argument("--format", default="jpg", choices=sorted(SUPPORTED_FORMATS), help="Generated image format.")
    parser.add_argument("--burst-size", default=5, type=int, help="Near-duplicate burst size.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = generate_synthetic_dataset(
        SyntheticDatasetConfig(
            output_dir=args.output,
            count=args.count,
            width=args.width,
            height=args.height,
            image_format=args.format,
            burst_size=args.burst_size,
        )
    )
    print(f"Generated {len(paths)} images in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
