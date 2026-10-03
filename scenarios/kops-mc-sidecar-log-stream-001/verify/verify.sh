#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify kops-mc-sidecar-log-stream-001
exec kops lab verify kops-mc-sidecar-log-stream-001 "$@"
