The cluster currently provisions volumes from the `standard` StorageClass whenever a claim does not name a class.
The platform team wants that role taken over by the `{{sc}}` StorageClass.

Make `{{sc}}` the default StorageClass, and make sure it is the only default.
Do not delete any StorageClass.
