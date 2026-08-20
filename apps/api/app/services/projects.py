from pathlib import Path

from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.local_paths import normalize_user_path
from app.core.project_roots import BLOCKED_ROOT_NAMES, registered_roots
from app.models.entities import Project, utc_now


def _is_under(path: Path, root: Path) -> bool:
    try:
        return path.resolve().is_relative_to(root.resolve())
    except (OSError, ValueError):
        return False


def create_project(
    session: Session,
    name: str,
    root_path: str | None = None,
    *,
    acknowledge_nonempty: bool = False,
) -> Project:
    settings = get_settings()
    projects_root = (settings.data_dir / "projects").resolve()
    project = Project(name=name, root_path=root_path or "")
    if root_path:
        project_root = Path(normalize_user_path(root_path)).expanduser().resolve()
        allowlist = settings.project_root_allowlist
        allowed_roots = [projects_root, *allowlist, *registered_roots()]
        if not any(_is_under(project_root, allowed) for allowed in allowed_roots):
            raise ValueError(
                f"Project root path must stay under the FramePilot data directory ({projects_root}) "
                "or an explicitly allowlisted location"
            )
        if str(project_root) in BLOCKED_ROOT_NAMES or project_root == project_root.anchor:
            raise ValueError("Project root path cannot target a system directory")
        if project_root.exists() and project_root.is_dir() and any(project_root.iterdir()) and not acknowledge_nonempty:
            raise ValueError(
                "Project root path is not empty; pass acknowledge_nonempty=true to use it anyway"
            )
        if project_root.exists() and not project_root.is_dir():
            raise ValueError("Project root path must be a usable local directory")
    else:
        project_root = projects_root / project.id
    try:
        project_root.mkdir(parents=True, exist_ok=True)
        for child in (
            "originals",
            "thumbnails",
            "previews",
            "exports",
            "exports/csv",
            "exports/zip",
            "exports/folders",
            "cache",
            "cache/hashes",
            "cache/embeddings",
            "cache/jobs",
            "logs",
        ):
            (project_root / child).mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise ValueError("Project root path must be a usable local directory") from error

    project.root_path = str(project_root)
    project.updated_at = utc_now()
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def list_projects(session: Session) -> list[Project]:
    return list(session.exec(select(Project).order_by(Project.created_at.desc())).all())
