from pathlib import Path

import git

from blogtuner.utils.logs import logger


def move_file_with_git_awareness(source: Path, destination: Path) -> Path:
    """
    Move a file or directory with Git awareness.

    Uses git mv if the file is in a Git repository, otherwise falls back to regular rename.
    """
    source, destination = Path(source), Path(destination)

    if not source.exists():
        raise FileNotFoundError(f"Source path does not exist: {source}")

    if destination.exists():
        raise FileExistsError(f"Destination path already exists: {destination}")

    try:
        # Try to handle with git if applicable
        repo = git.Repo(source.absolute(), search_parent_directories=True)
        rel_source = str(source.absolute().relative_to(repo.working_dir))

        if rel_source in [item[0] for item in repo.index.entries]:
            repo.git.mv(source.absolute(), destination.absolute())
            return destination
    except (git.InvalidGitRepositoryError, git.NoSuchPathError, ValueError):
        pass  # Not a git repo or file not tracked

    # Regular file system move
    source.rename(destination)
    logger.info(f"Renamed file to {destination}")
    return destination
