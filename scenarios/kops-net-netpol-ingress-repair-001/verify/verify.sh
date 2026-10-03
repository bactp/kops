#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify kops-net-netpol-ingress-repair-001
exec kops lab verify kops-net-netpol-ingress-repair-001 "$@"
