#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify kops-wl-rollout-undo-to-revision-001
exec kops lab verify kops-wl-rollout-undo-to-revision-001 "$@"
