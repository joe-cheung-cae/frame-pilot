from pathlib import Path

from sqlmodel import Session, select

from app.core.config import get_settings
from app.models.entities import Project, utc_now


def create_project(session: Session, name: str, root_path: str | None = None) -> Project:
    settings = get_settings()
    project = Project(name=name, root_path=root_path or "")
    session.add(project)
    session.commit()
    session.refresh(project)

    project_root = Path(root_path) if root_path else settings.data_dir / "projects" / project.id
    project_root.mkdir(parents=True, exist_ok=True)
    for child in (
        "originals",
        "thumbnails",
        "previews",
        "exports",
        "cache",
        "cache/hashes",
        "cache/embeddings",
        "cache/jobs",
        "logs",
    ):
        (project_root / child).mkdir(parents=True, exist_ok=True)
    project.root_path = str(project_root)
    project.updated_at = utc_now()
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def list_projects(session: Session) -> list[Project]:
    return list(session.exec(select(Project).order_by(Project.created_at.desc())).all())
