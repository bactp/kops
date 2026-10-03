#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify kops-obs-probe-startup-001
exec kops lab verify kops-obs-probe-startup-001 "$@"
