#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify ckad-cfg-projected-volume-001
exec kops lab verify ckad-cfg-projected-volume-001 "$@"
