#!/usr/bin/env bash
# Thin wrapper: grade a live lab. Usage: kops lab verify ckad-deploy-canary-share-001
exec kops lab verify ckad-deploy-canary-share-001 "$@"
