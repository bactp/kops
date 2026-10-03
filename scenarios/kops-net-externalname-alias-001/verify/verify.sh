#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify kops-net-externalname-alias-001
exec kops lab verify kops-net-externalname-alias-001 "$@"
