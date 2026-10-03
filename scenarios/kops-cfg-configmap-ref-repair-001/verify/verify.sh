#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify kops-cfg-configmap-ref-repair-001
exec kops lab verify kops-cfg-configmap-ref-repair-001 "$@"
