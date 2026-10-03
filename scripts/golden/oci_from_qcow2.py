#!/usr/bin/env python3
"""Wrap a qcow2 disk as an OCI image KubeVirt can use as a containerDisk (file at /disk/<name>.qcow2).

usage: oci_from_qcow2.py DISK.qcow2 OUT.tar IMAGE_REF   e.g. localhost/kops/node-golden:v3
No docker or registry needed: the tar is imported with `ctr -n k8s.io images import --index-name IMAGE_REF`.
"""
import hashlib, json, os, shutil, sys, tarfile, tempfile

src, out_tar, ref = sys.argv[1:4]
work = tempfile.mkdtemp(prefix="oci-")
blobs = os.path.join(work, "blobs", "sha256"); os.makedirs(blobs)
layer = os.path.join(work, "layer.tar")
name = os.path.basename(src)
with tarfile.open(layer, "w", format=tarfile.PAX_FORMAT) as t:
    d = tarfile.TarInfo("disk"); d.type = tarfile.DIRTYPE; d.mode = 0o755; d.uid = d.gid = 107; t.addfile(d)
    ti = tarfile.TarInfo(f"disk/{name}"); ti.size = os.path.getsize(src); ti.mode = 0o644; ti.uid = ti.gid = 107
    with open(src, "rb") as f: t.addfile(ti, f)
h = hashlib.sha256()
with open(layer, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
ld, lsize = h.hexdigest(), os.path.getsize(layer)
shutil.move(layer, os.path.join(blobs, ld))
def blob(data: bytes):
    d = hashlib.sha256(data).hexdigest(); open(os.path.join(blobs, d), "wb").write(data); return d, len(data)
cd, cs = blob(json.dumps({"architecture": "amd64", "os": "linux", "config": {},
                          "rootfs": {"type": "layers", "diff_ids": [f"sha256:{ld}"]}}).encode())
md, ms = blob(json.dumps({"schemaVersion": 2, "mediaType": "application/vnd.oci.image.manifest.v1+json",
    "config": {"mediaType": "application/vnd.oci.image.config.v1+json", "digest": f"sha256:{cd}", "size": cs},
    "layers": [{"mediaType": "application/vnd.oci.image.layer.v1.tar", "digest": f"sha256:{ld}", "size": lsize}]}).encode())
json.dump({"schemaVersion": 2, "manifests": [{"mediaType": "application/vnd.oci.image.manifest.v1+json",
    "digest": f"sha256:{md}", "size": ms,
    "annotations": {"org.opencontainers.image.ref.name": ref.split(":")[-1], "io.containerd.image.name": ref}}]},
    open(os.path.join(work, "index.json"), "w"))
json.dump({"imageLayoutVersion": "1.0.0"}, open(os.path.join(work, "oci-layout"), "w"))
with tarfile.open(out_tar, "w") as t: t.add(work, arcname=".")
shutil.rmtree(work)
print(f"wrote {out_tar} ({os.path.getsize(out_tar) / 2**30:.2f} GiB) for {ref}")
