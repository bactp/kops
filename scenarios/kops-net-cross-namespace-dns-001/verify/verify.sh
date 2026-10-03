#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify kops-net-cross-namespace-dns-001
exec kops lab verify kops-net-cross-namespace-dns-001 "$@"
