#!/usr/bin/env bash
# macOS: avoids SIGBUS / "pack-objects died of signal 10" during push for some
# setups (iCloud-backed dirs, certain Xcode git builds). See git-env GIT_MMAP_LIMIT.
set -euo pipefail
export GIT_MMAP_LIMIT=0
cd "$(dirname "$0")/.."
exec git push "$@"
