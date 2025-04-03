import os

# List of items to exclude (files or directories)
EXCLUDED_ITEMS = {
    "__",  # Skip anything starting with __
    ".coverage",
    ".ruff_cache",
    ".pytest_cache",
    ".coverageDockerfile",
    "Makefile",
    "cspell",
    "docker-compose",
    "run.sh",
    "fly.toml",
    "mkdocs.yml",
    "index",
    ".dockerignore",
    ".env",
    ".pre",
    ".python",
    "LICENSE",
    "Dockerfile",
    "assets",
    "conftest.py",
    "coverage",
    "coverage.xml",
    "coverage_html",
    "site",
    ".venv",
    "calibration_service.egg-info",
    ".DS_Store",
    "alembic",
    ".vscode",
    ".idea",
    ".git",
    ".run",
    "tests/__pycache__",  # Add more items if needed
    "uv.lock",
    "pytest.ini",
}


def generate_tree(dir_path: str, prefix=""):  # pyright: ignore [reportMissingParameterType]
    tree = []
    contents = sorted(
        # Include items not in the exclusion list
        [
            item
            for item in os.listdir(dir_path)  # noqa: PTH208
            if not any(
                item.startswith(exclude) or item == exclude
                for exclude in EXCLUDED_ITEMS
            )
        ]
    )
    for ix, item in enumerate(contents):
        path = os.path.join(dir_path, item)  # noqa: PTH118
        connector = "└── " if ix == len(contents) - 1 else "├── "
        tree.append(f"{prefix}{connector}{item}")
        # Recurse into subdirectories if the item is a directory
        if os.path.isdir(path):  # noqa: PTH112
            next_prefix = "    " if ix == len(contents) - 1 else "│   "
            tree.extend(generate_tree(path, prefix=prefix + next_prefix))
    return tree


if __name__ == "__main__":
    directory = "."  # Change this to the target directory
    print("\n".join(generate_tree(directory)))
