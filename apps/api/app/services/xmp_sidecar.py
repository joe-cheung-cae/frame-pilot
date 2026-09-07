from pathlib import Path
from xml.etree import ElementTree as ET

NS_X = "adobe:ns:meta/"
NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NS_XMP = "http://ns.adobe.com/xap/1.0/"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_XML = "http://www.w3.org/XML/1998/namespace"

XMP_STATUS_LABELS = {
    "Pick": "Green",
    "Maybe": "Yellow",
    "Reject": "Red",
}
VALID_USER_STATUSES = frozenset({"Pick", "Maybe", "Reject", "Unreviewed"})


def clamp_star_rating(value: object) -> int:
    try:
        rating = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        rating = 0
    return max(0, min(5, rating))


def normalize_user_status(value: object) -> str:
    text = str(value or "Unreviewed")
    if text in VALID_USER_STATUSES:
        return text
    return "Unreviewed"


def xmp_sidecar_filename(exported_filename: str) -> str:
    return f"{Path(exported_filename).name}.xmp"


def build_xmp_packet(
    *,
    photo_id: str,
    exported_filename: str,
    user_status: str,
    star_rating: object,
) -> str:
    ET.register_namespace("x", NS_X)
    ET.register_namespace("rdf", NS_RDF)
    ET.register_namespace("xmp", NS_XMP)
    ET.register_namespace("dc", NS_DC)

    status = normalize_user_status(user_status)
    rating = clamp_star_rating(star_rating)
    filename = Path(exported_filename).name

    xmpmeta = ET.Element(f"{{{NS_X}}}xmpmeta")
    rdf = ET.SubElement(xmpmeta, f"{{{NS_RDF}}}RDF")
    description = ET.SubElement(rdf, f"{{{NS_RDF}}}Description")
    description.set(f"{{{NS_XMP}}}Rating", str(rating))
    label = XMP_STATUS_LABELS.get(status)
    if label is not None:
        description.set(f"{{{NS_XMP}}}Label", label)

    title = ET.SubElement(description, f"{{{NS_DC}}}title")
    alt = ET.SubElement(title, f"{{{NS_RDF}}}Alt")
    title_li = ET.SubElement(alt, f"{{{NS_RDF}}}li")
    title_li.set(f"{{{NS_XML}}}lang", "x-default")
    title_li.text = filename

    identifier = ET.SubElement(description, f"{{{NS_DC}}}identifier")
    identifier.text = str(photo_id)

    subject = ET.SubElement(description, f"{{{NS_DC}}}subject")
    bag = ET.SubElement(subject, f"{{{NS_RDF}}}Bag")
    subject_li = ET.SubElement(bag, f"{{{NS_RDF}}}li")
    subject_li.text = status

    xml_bytes = ET.tostring(xmpmeta, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")


def write_xmp_sidecar(
    path: Path,
    *,
    photo_id: str,
    exported_filename: str,
    user_status: str,
    star_rating: object,
) -> Path:
    path.write_text(
        build_xmp_packet(
            photo_id=str(photo_id),
            exported_filename=exported_filename,
            user_status=user_status,
            star_rating=star_rating,
        ),
        encoding="utf-8",
    )
    return path
