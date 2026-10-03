#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify kops-net-netpol-egress-dns-001
exec kops lab verify kops-net-netpol-egress-dns-001 "$@"
