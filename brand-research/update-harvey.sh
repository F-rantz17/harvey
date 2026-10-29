#!/bin/bash
# Pull the latest Harvey from the original project and replay your fixes on top.
#   bash ~/"Claude Projects"/harvey/brand-research/update-harvey.sh
# Stops safely (changes nothing) if your fixes clash with the new upstream code.
set -eu
cd "$(dirname "$0")/.."
branch="$(git rev-parse --abbrev-ref HEAD)"
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "You have unsaved code changes; commit them first."; exit 1; }
git fetch -q upstream
new="$(git rev-list --count HEAD..upstream/main)"
if [ "$new" = "0" ]; then echo "Already up to date with Harvey."; exit 0; fi
echo "Harvey has $new new commit(s). Replaying your fixes on top..."
if ! git rebase -q upstream/main; then
  git rebase --abort
  echo "Your fixes clash with the new Harvey code. Nothing was changed."
  echo "Ask Claude: \"update Harvey and resolve the conflicts\"."
  exit 2
fi
echo "Updated. Ask Claude to run the tests, then push:  git push --force-with-lease origin $branch"
