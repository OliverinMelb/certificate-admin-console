"""Create an explicit, new performance database; never touches the default demo DB."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))

from app.database import connect, initialize
from app.issuance import initialize_issuance


def generate(path: Path, count: int):
    if count < 12:
        raise ValueError('rows must be at least 12 (the persistent demo baseline)')
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive create also refuses a symlink/another process racing the same name.
    with path.open('xb'):
        pass
    initialize(path)
    with connect(path) as db, db:
        initialize_issuance(db)
        for start in range(0, count - 12, 1000):
            indexes = range(start, min(start + 1000, count - 12))
            db.executemany('INSERT INTO learner VALUES (?, ?, ?)',
                           [(f'perf-learner-{i:06}', 'east', f'Perf Learner {i // 2:06}') for i in indexes])
            db.executemany('INSERT INTO enrollment VALUES (?, ?, ?, ?, ?)',
                           [(f'perf-enrollment-{i:06}', 'east', 'east-safety', f'perf-learner-{i:06}', 1)
                            for i in indexes])
            db.executemany('INSERT INTO certificate VALUES (?, ?, ?, ?, ?, ?, ?)',
                           [(f'perf-cert-{i:06}', 'east', f'PERF-{i:06}', 'east-safety',
                             f'perf-learner-{i:06}', f'2026-01-{i % 28 + 1:02}T13:30:00Z',
                             'REVOKED' if i % 11 == 0 else 'ACTIVE') for i in indexes])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True, type=Path)
    parser.add_argument('--rows', type=int, default=100000)
    args = parser.parse_args()
    try:
        generate(args.database.resolve(), args.rows)
    except (FileExistsError, ValueError) as error:
        parser.exit(2, f'{error}\n')
    print(json.dumps({'database': str(args.database.resolve()), 'east_rows': args.rows, 'west_rows': 4}))


if __name__ == '__main__':
    main()
