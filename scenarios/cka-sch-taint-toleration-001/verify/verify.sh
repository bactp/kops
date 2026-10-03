#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify cka-sch-taint-toleration-001
exec kops lab verify cka-sch-taint-toleration-001 "$@"
