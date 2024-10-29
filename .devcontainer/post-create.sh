#!/bin/zsh
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type pre-push