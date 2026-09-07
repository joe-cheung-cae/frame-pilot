import hashlib
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from app.services.exporting import copy_selected_files, zip_selected_files

NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NS_XMP = "http://ns.adobe.com/xap/1.0/"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_X = "adobe:ns:meta/"


def parse_xmp_fields(xml: str) -> dict[str, str | None]:
    root = ET.fromstring(xml)
    description = root.find(f".//{{{NS_RDF}}}Description")
    assert description is not None
    title = description.find(f".//{{{NS_DC}}}title//{{{NS_RDF}}}li")
    if title is None:
        title = description.find(f"{{{NS_DC}}}title")
    identifier = description.find(f"{{{NS_DC}}}identifier")
    subject = description.find(f".//{{{NS_DC}}}subject//{{{NS_RDF}}}li")
    return {
        "rating": description.get(f"{{{NS_XMP}}}Rating"),
        "label": description.get(f"{{{NS_XMP}}}Label"),
        "title": None if title is None else title.text,
        "identifier": None if identifier is None else identifier.text,
        "subject": None if subject is None else subject.text,
    }


def _fingerprint(path: Path) -> tuple[int, int, str]:
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()


def test_xmp_packet_maps_pick_maybe_reject_unreviewed_and_star_bounds():
    from app.services.xmp_sidecar import build_xmp_packet

    cases = [
        ("Pick", 5, "5", "Green", "Pick"),
        ("Maybe", 0, "0", "Yellow", "Maybe"),
        ("Reject", 3, "3", "Red", "Reject"),
        ("Unreviewed", 4, "4", None, "Unreviewed"),
    ]
    for status, stars, rating, label, subject in cases:
        xml = build_xmp_packet(
            photo_id=f"photo-{status}",
            exported_filename="hero.jpg",
            user_status=status,
            star_rating=stars,
        )
        fields = parse_xmp_fields(xml)
        assert fields["rating"] == rating
        assert fields["label"] == label
        assert fields["subject"] == subject
        assert fields["title"] == "hero.jpg"
        assert fields["identifier"] == f"photo-{status}"
        assert "overall_score" not in xml
        assert "GPS" not in xml
        assert "-1" not in xml
        assert NS_X in xml
        assert NS_XMP in xml
        assert NS_DC in xml
        assert NS_RDF in xml


def test_xmp_packet_clamps_star_rating_and_escapes_xml():
    from app.services.xmp_sidecar import build_xmp_packet

    xml = build_xmp_packet(
        photo_id="id<&",
        exported_filename='hero<"&.jpg',
        user_status="Pick",
        star_rating=99,
    )
    fields = parse_xmp_fields(xml)
    assert fields["rating"] == "5"
    assert fields["title"] == 'hero<"&.jpg'
    assert fields["identifier"] == "id<&"

    xml_low = build_xmp_packet(
        photo_id="low",
        exported_filename="low.jpg",
        user_status="Reject",
        star_rating=-2,
    )
    assert parse_xmp_fields(xml_low)["rating"] == "0"
    assert parse_xmp_fields(xml_low)["label"] == "Red"


def test_write_xmp_sidecar_uses_exported_basename_plus_xmp(tmp_path):
    from app.services.xmp_sidecar import write_xmp_sidecar

    target = tmp_path / "hero.jpg.xmp"
    write_xmp_sidecar(
        target,
        photo_id="p1",
        exported_filename="hero.jpg",
        user_status="Pick",
        star_rating=5,
    )
    assert target.is_file()
    assert parse_xmp_fields(target.read_text(encoding="utf-8"))["title"] == "hero.jpg"


def test_copy_and_zip_omit_xmp_by_default_and_leave_originals(tmp_path):
    originals = tmp_path / "originals"
    originals.mkdir()
    source = originals / "hero.jpg"
    payload = b"original-bytes"
    source.write_bytes(payload)
    before = _fingerprint(source)
    photos = [
        {
            "id": "p1",
            "filename": "hero.jpg",
            "original_path": str(source),
            "project_copy_path": str(source),
            "user_status": "Pick",
            "star_rating": 5,
        }
    ]

    copy_selected_files(tmp_path / "selected", photos)
    zip_path = zip_selected_files(tmp_path / "selected.zip", photos)
    zip_off = zip_selected_files(tmp_path / "selected-false.zip", photos, include_xmp=False)

    assert list((tmp_path / "selected").glob("*.xmp")) == []
    assert list(tmp_path.rglob("*.xmp")) == []
    with zipfile.ZipFile(zip_path) as archive:
        assert archive.namelist() == ["hero.jpg"]
        assert archive.read("hero.jpg") == payload
    with zipfile.ZipFile(zip_off) as archive:
        assert archive.namelist() == ["hero.jpg"]
    assert _fingerprint(source) == before


def test_folder_export_writes_xmp_next_to_copies_not_originals(tmp_path):
    camera = tmp_path / "camera-card"
    camera.mkdir()
    originals = tmp_path / "project" / "originals"
    originals.mkdir(parents=True)
    payload = b"camera-original"
    camera_file = camera / "hero.jpg"
    project_copy = originals / "hero.jpg"
    camera_file.write_bytes(payload)
    project_copy.write_bytes(payload)
    camera_before = _fingerprint(camera_file)
    copy_before = _fingerprint(project_copy)
    photos = [
        {
            "id": "pick-id",
            "filename": "hero.jpg",
            "original_path": str(camera_file),
            "project_copy_path": str(project_copy),
            "user_status": "Pick",
            "star_rating": 5,
        }
    ]

    target = copy_selected_files(
        tmp_path / "exports" / "folders" / "selected-1",
        photos,
        project_root=tmp_path / "project",
        include_xmp=True,
    )

    sidecar = target / "hero.jpg.xmp"
    assert (target / "hero.jpg").read_bytes() == payload
    assert sidecar.is_file()
    fields = parse_xmp_fields(sidecar.read_text(encoding="utf-8"))
    assert fields == {
        "rating": "5",
        "label": "Green",
        "title": "hero.jpg",
        "identifier": "pick-id",
        "subject": "Pick",
    }
    assert list(originals.glob("*.xmp")) == []
    assert list(camera.glob("*.xmp")) == []
    assert _fingerprint(camera_file) == camera_before
    assert _fingerprint(project_copy) == copy_before


def test_folder_export_duplicate_names_get_matching_sidecars(tmp_path):
    originals = tmp_path / "project" / "originals"
    originals.mkdir(parents=True)
    first = originals / "frame.jpg"
    second_dir = originals / "nested"
    second_dir.mkdir()
    second = second_dir / "frame.jpg"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    photos = [
        {
            "id": "one",
            "filename": "frame.jpg",
            "original_path": str(first),
            "project_copy_path": str(first),
            "user_status": "Maybe",
            "star_rating": 0,
        },
        {
            "id": "two",
            "filename": "frame.jpg",
            "original_path": str(second),
            "project_copy_path": str(second),
            "user_status": "Reject",
            "star_rating": 5,
        },
    ]

    target = copy_selected_files(tmp_path / "selected", photos, project_root=tmp_path / "project", include_xmp=True)

    assert (target / "frame.jpg").read_bytes() == b"first"
    assert (target / "frame-1.jpg").read_bytes() == b"second"
    first_fields = parse_xmp_fields((target / "frame.jpg.xmp").read_text(encoding="utf-8"))
    second_fields = parse_xmp_fields((target / "frame-1.jpg.xmp").read_text(encoding="utf-8"))
    assert first_fields["identifier"] == "one"
    assert first_fields["title"] == "frame.jpg"
    assert first_fields["label"] == "Yellow"
    assert second_fields["identifier"] == "two"
    assert second_fields["title"] == "frame-1.jpg"
    assert second_fields["label"] == "Red"
    assert not (target / "frame.xmp").exists()
    assert list((tmp_path / "project" / "originals").rglob("*.xmp")) == []


def test_zip_export_includes_deflated_xmp_and_stored_original_bytes(tmp_path):
    originals = tmp_path / "project" / "originals"
    originals.mkdir(parents=True)
    source = originals / "hero.jpg"
    payload = b"zip-original-bytes"
    source.write_bytes(payload)
    before = _fingerprint(source)
    photos = [
        {
            "id": "zip-id",
            "filename": "hero.jpg",
            "original_path": str(source),
            "project_copy_path": str(source),
            "user_status": "Unreviewed",
            "star_rating": 0,
        }
    ]

    zip_path = zip_selected_files(
        tmp_path / "exports" / "zip" / "selected-1.zip",
        photos,
        project_root=tmp_path / "project",
        include_xmp=True,
    )

    with zipfile.ZipFile(zip_path) as archive:
        assert sorted(archive.namelist()) == ["hero.jpg", "hero.jpg.xmp"]
        image_info = archive.getinfo("hero.jpg")
        xmp_info = archive.getinfo("hero.jpg.xmp")
        assert image_info.compress_type == zipfile.ZIP_STORED
        assert xmp_info.compress_type == zipfile.ZIP_DEFLATED
        assert archive.read("hero.jpg") == payload
        fields = parse_xmp_fields(archive.read("hero.jpg.xmp").decode("utf-8"))
    assert fields["label"] is None
    assert fields["subject"] == "Unreviewed"
    assert fields["rating"] == "0"
    assert fields["identifier"] == "zip-id"
    assert _fingerprint(source) == before
    assert list(originals.glob("*.xmp")) == []
