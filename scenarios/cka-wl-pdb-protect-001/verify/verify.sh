#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify cka-wl-pdb-protect-001
exec kops lab verify cka-wl-pdb-protect-001 "$@"
