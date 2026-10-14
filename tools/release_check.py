"""A narrow publication check; manual content review is still required."""
from pathlib import Path
import re
import subprocess

ALLOWED = {
    '.gitignore', '.github/workflows/check.yml', 'README.md', 'SECURITY.md',
    'docs/DESIGN.md', 'docs/PROVENANCE.md', 'showcase/__init__.py',
    'showcase/__main__.py', 'showcase/queue.py', 'showcase/commerce.py',
    'showcase/evidence.py', 'sql/jobs.sql', 'sql/commerce.sql',
    'sql/reconciliation.sql', 'sql/cash_summary.sql', 'tests/test_showcase.py',
    'tools/release_check.py',
}
PATTERNS = [
    r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
    r'gh[pousr]_[A-Za-z0-9]{20,}',
    r'AKIA[A-Z0-9]{16}',
    r'sk-[A-Za-z0-9]{24,}',
    r'/Users/',
    r'(?:business-private|personal-private|runtime\.sqlite)',
]


def main():
    root = Path(__file__).resolve().parents[1]
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
    paths = set(filter(None, paths))
    errors = []
    if paths != ALLOWED:
        errors.append('Tracked files differ from the reviewed release allowlist')
    for name in sorted(paths & ALLOWED):
        path = root / name
        if path.is_symlink():
            errors.append(f'{name}: symlink is not permitted')
            continue
        # The checker contains pattern definitions, not real confidential values.
        if name == 'tools/release_check.py':
            continue
        content = path.read_text()
        if any(re.search(pattern, content) for pattern in PATTERNS):
            errors.append(f'{name}: suspicious literal requires review')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Publication check passed for {len(paths)} allowlisted files; manual review still required.')


if __name__ == '__main__':
    main()
