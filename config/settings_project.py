from dataclasses import dataclass
from pathlib import Path


def find_project_root() -> Path:
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Project root not found")


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    root: Path
    config: Path
    databases: Path
    sql_scripts: Path
    data: Path

    @classmethod
    def build(cls) -> "ProjectPaths":
        root = find_project_root()
        return cls(
            root=root,
            config=root / "config",
            databases=root / "databases",
            sql_scripts=root / "sql_scripts",
            data=root / "data",
        )



