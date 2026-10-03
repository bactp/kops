#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify kops-sto-pvc-reference-repair-001
exec kops lab verify kops-sto-pvc-reference-repair-001 "$@"
