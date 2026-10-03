The `{{app}}` Deployment in namespace `{{ns}}` serves the directory `/etc/site` over HTTP (Service port 80). The directory currently
holds only `index.html`, which comes from the ConfigMap `{{app}}-page`.

Make the **same directory** also contain a file `token.txt` with the value of the key `token` of the Secret `{{app}}-token`
(the application reads both files from `/etc/site`). Use one volume only that combines both sources; keep the image and the mount path.
