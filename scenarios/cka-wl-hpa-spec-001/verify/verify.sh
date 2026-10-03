#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify cka-wl-hpa-spec-001
exec kops lab verify cka-wl-hpa-spec-001 "$@"
