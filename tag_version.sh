#!/bin/bash
set -e

latest_commit=$(git rev-parse HEAD)
previous_commit=$(git rev-parse HEAD~1)

prev_version=$(git show "$previous_commit":pyproject.toml | grep '^version =' | awk -F '"' '{print $2}')
curr_version=$(git show "$latest_commit":pyproject.toml | grep '^version =' | awk -F '"' '{print $2}')

if [ "$prev_version" != "$curr_version" ]; then
    echo "Version changed from $prev_version to $curr_version. Creating tag v$curr_version..."
    git tag -a "v$curr_version" -m "Tag version v$curr_version"
    git push origin "v$curr_version"
else
    echo "Version did not change. No tag created."
fi
