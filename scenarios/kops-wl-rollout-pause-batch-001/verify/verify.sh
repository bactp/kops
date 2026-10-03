#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify kops-wl-rollout-pause-batch-001
exec kops lab verify kops-wl-rollout-pause-batch-001 "$@"
