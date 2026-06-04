from app.services.grouping import group_similar_photos


def test_grouping_uses_similarity_and_time_window():
    photos = [
        {"id": "a", "filename": "IMG_0001.jpg", "capture_time": "2026-01-01T10:00:00", "embedding": [1.0, 0.0]},
        {"id": "b", "filename": "IMG_0002.jpg", "capture_time": "2026-01-01T10:00:02", "embedding": [0.99, 0.01]},
        {"id": "c", "filename": "IMG_0100.jpg", "capture_time": "2026-01-01T11:00:00", "embedding": [1.0, 0.0]},
        {"id": "d", "filename": "IMG_0200.jpg", "capture_time": "2026-01-01T11:00:03", "embedding": [0.0, 1.0]},
    ]

    groups = group_similar_photos(photos, similarity_threshold=0.95, max_time_gap_seconds=10)

    assert [group.photo_ids for group in groups] == [["a", "b"], ["c"], ["d"]]


def test_grouping_falls_back_to_filename_order_without_capture_time():
    photos = [
        {"id": "2", "filename": "B.jpg", "embedding": [1.0, 0.0]},
        {"id": "1", "filename": "A.jpg", "embedding": [1.0, 0.0]},
    ]

    groups = group_similar_photos(photos, similarity_threshold=0.95)

    assert groups[0].photo_ids == ["1", "2"]


def test_grouping_uses_union_find_for_non_adjacent_burst_frames():
    photos = [
        {
            "id": "a",
            "filename": "IMG_0001.jpg",
            "capture_time": "2026-01-01T10:00:00",
            "embedding": [1.0, 0.0],
            "width": 6000,
            "height": 4000,
            "camera_model": "Camera A",
            "focal_length": "35",
        },
        {
            "id": "b",
            "filename": "IMG_0002.jpg",
            "capture_time": "2026-01-01T10:00:01",
            "embedding": [0.7, 0.7],
            "width": 6000,
            "height": 4000,
            "camera_model": "Camera A",
            "focal_length": "35",
        },
        {
            "id": "c",
            "filename": "IMG_0003.jpg",
            "capture_time": "2026-01-01T10:00:02",
            "embedding": [0.99, 0.01],
            "width": 6000,
            "height": 4000,
            "camera_model": "Camera A",
            "focal_length": "35",
        },
    ]

    groups = group_similar_photos(photos, similarity_threshold=0.95, max_time_gap_seconds=10)

    assert [group.photo_ids for group in groups] == [["a", "c"], ["b"]]


def test_grouping_avoids_over_merging_across_metadata_mismatch():
    photos = [
        {
            "id": "wide",
            "filename": "IMG_0001.jpg",
            "capture_time": "2026-01-01T10:00:00",
            "embedding": [1.0, 0.0],
            "width": 6000,
            "height": 4000,
            "camera_model": "Camera A",
            "focal_length": "24",
        },
        {
            "id": "tele",
            "filename": "IMG_0002.jpg",
            "capture_time": "2026-01-01T10:00:01",
            "embedding": [1.0, 0.0],
            "width": 6000,
            "height": 4000,
            "camera_model": "Camera A",
            "focal_length": "200",
        },
        {
            "id": "other-camera",
            "filename": "IMG_0003.jpg",
            "capture_time": "2026-01-01T10:00:02",
            "embedding": [1.0, 0.0],
            "width": 6000,
            "height": 4000,
            "camera_model": "Camera B",
            "focal_length": "24",
        },
    ]

    groups = group_similar_photos(photos, similarity_threshold=0.95, max_time_gap_seconds=10)

    assert [group.photo_ids for group in groups] == [["wide"], ["tele"], ["other-camera"]]


def test_grouping_avoids_over_merging_across_lens_mismatch():
    photos = [
        {
            "id": "prime",
            "filename": "IMG_0001.jpg",
            "capture_time": "2026-01-01T10:00:00",
            "embedding": [1.0, 0.0],
            "width": 6000,
            "height": 4000,
            "camera_model": "Camera A",
            "lens_model": "Prime 35mm",
            "focal_length": "35",
        },
        {
            "id": "zoom",
            "filename": "IMG_0002.jpg",
            "capture_time": "2026-01-01T10:00:01",
            "embedding": [1.0, 0.0],
            "width": 6000,
            "height": 4000,
            "camera_model": "Camera A",
            "lens_model": "Zoom 24-70mm",
            "focal_length": "35",
        },
    ]

    groups = group_similar_photos(photos, similarity_threshold=0.95, max_time_gap_seconds=10)

    assert [group.photo_ids for group in groups] == [["prime"], ["zoom"]]


def test_grouping_uses_filename_proximity_without_capture_time():
    photos = [
        {"id": "a", "filename": "IMG_0001.jpg", "embedding": [1.0, 0.0]},
        {"id": "b", "filename": "IMG_0002.jpg", "embedding": [1.0, 0.0]},
        {"id": "c", "filename": "IMG_0100.jpg", "embedding": [1.0, 0.0]},
    ]

    groups = group_similar_photos(photos, similarity_threshold=0.95, max_filename_gap=3)

    assert [group.photo_ids for group in groups] == [["a", "b"], ["c"]]


def test_grouping_uses_filename_proximity_when_burst_metadata_is_incomplete():
    photos = [
        {
            "id": "missing-middle",
            "filename": "IMG_0101.jpg",
            "embedding": [1.0, 0.0],
            "perceptual_hash": "0000000000000000",
            "width": 6000,
            "height": 4000,
            "camera_model": "Camera A",
            "focal_length": "35",
        },
        {
            "id": "dated-neighbor",
            "filename": "IMG_0102.jpg",
            "capture_time": "2026-01-01T10:00:02",
            "embedding": [0.0, 1.0],
            "perceptual_hash": "0000000000000001",
            "width": 6000,
            "height": 4000,
            "camera_model": "Camera A",
            "focal_length": "35",
        },
        {
            "id": "unrelated",
            "filename": "IMG_0200.jpg",
            "embedding": [1.0, 0.0],
            "perceptual_hash": "0000000000000000",
            "width": 6000,
            "height": 4000,
            "camera_model": "Camera A",
            "focal_length": "35",
        },
    ]

    groups = group_similar_photos(photos, max_filename_gap=3, max_hash_distance=4)

    assert [group.photo_ids for group in groups] == [["missing-middle", "dated-neighbor"], ["unrelated"]]


def test_grouping_uses_perceptual_hash_distance_when_available():
    photos = [
        {
            "id": "a",
            "filename": "IMG_0001.jpg",
            "capture_time": "2026-01-01T10:00:00",
            "embedding": [1.0, 0.0],
            "perceptual_hash": "0000000000000000",
        },
        {
            "id": "b",
            "filename": "IMG_0002.jpg",
            "capture_time": "2026-01-01T10:00:01",
            "embedding": [0.0, 1.0],
            "perceptual_hash": "000000000000000f",
        },
        {
            "id": "c",
            "filename": "IMG_0003.jpg",
            "capture_time": "2026-01-01T10:00:02",
            "embedding": [1.0, 0.0],
            "perceptual_hash": "ffffffffffffffff",
        },
    ]

    groups = group_similar_photos(photos, similarity_threshold=0.95, max_hash_distance=8)

    assert [group.photo_ids for group in groups] == [["a", "b"], ["c"]]


def test_grouping_splits_transitive_matches_when_time_span_is_too_large():
    photos = [
        {
            "id": "a",
            "filename": "IMG_0001.jpg",
            "capture_time": "2026-01-01T10:00:00",
            "embedding": [1.0, 0.0],
            "perceptual_hash": "0000000000000000",
        },
        {
            "id": "b",
            "filename": "IMG_0002.jpg",
            "capture_time": "2026-01-01T10:00:20",
            "embedding": [1.0, 0.0],
            "perceptual_hash": "0000000000000000",
        },
        {
            "id": "c",
            "filename": "IMG_0003.jpg",
            "capture_time": "2026-01-01T10:00:40",
            "embedding": [1.0, 0.0],
            "perceptual_hash": "0000000000000000",
        },
    ]

    groups = group_similar_photos(photos, max_time_gap_seconds=30)

    assert [group.photo_ids for group in groups] == [["a", "b"], ["c"]]
