In namespace `{{ns}}`, pods labelled `app=client` are restricted by an egress NetworkPolicy. They are meant to call the
`{{app}}` Service by name (`http://{{app}}/`, Service port 80), but the calls fail before even connecting.

Fix it so that the client reaches `{{app}}` by name.

Constraints:
- The client must remain unable to reach the `{{other}}` Service in the same namespace.
- Keep the egress policy; do not replace it with an allow-all rule.
