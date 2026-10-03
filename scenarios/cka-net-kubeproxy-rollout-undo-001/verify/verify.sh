#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify cka-net-kubeproxy-rollout-undo-001
exec kops lab verify cka-net-kubeproxy-rollout-undo-001 "$@"
