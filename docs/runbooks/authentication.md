# Authentication and external notebook access

## Databrix accounts

Django sessions are authoritative. Next.js forwards browser session cookies to the versioned API.
Unsafe API operations require CSRF protection, including anonymous login/invitation/reset endpoints.
Local registration is invitation-only. An administrator invites a student or instructor, optionally into a course.
New local users choose a password and verify their email before login; passwords must satisfy Django validators.
Existing accounts must sign in before accepting an invitation for their address; account IDs/password hashes stay intact.
Password-reset responses do not disclose whether an email exists.
Users may edit names; administrator deactivation retains academic history.
CourseStaff assignments and per-module teachers determine authorization independently of global instructor flags.

## Institutional SSO gateway

Enable SSO only after configuring a trusted institutional gateway and reviewing its identity attributes.
`/auth/institutional/login/` stores a single-use session nonce and redirects to `SSO_LOGIN_URL`.
The authenticated gateway returns to `/auth/institutional/callback/?state=...` with:

- X-Databrix-Sso-Secret (shared runtime secret matching SSO_GATEWAY_SECRET)
- X-Databrix-Sso-Issuer and X-Databrix-Sso-Subject (stable verified institutional identifiers)
- X-Databrix-Sso-Email, X-Databrix-Sso-First-Name, X-Databrix-Sso-Last-Name

The callback requires the nonce and secret. Other routes never authenticate from identity headers.
The provided nginx strips those headers on public traffic, including the callback.
A deployment gateway must deliver the callback through a separate restricted internal ingress/location,
validate institutional authentication, set the headers itself, and prevent direct public access to that path.
Do not weaken the general proxy header stripping to make an untrusted callback work.
The local stack intentionally has SSO disabled; provider integration is an external acceptance gate.

Existing issuer/subject bindings resolve to the same Databrix user.
When an address already exists without a binding, Databrix returns 409 rather than automatically merging identities.
An authenticated user may link through the callback, or an operator may bind reviewed identities:

```bash
python manage.py link_identity --user-id 42 --issuer institution --subject verified-stable-subject
```

Do not invent historical subjects from an email address.
Django allauth supplies verified email records and closes public signup; API workflows use the shared Django session.
Only the versioned account API is published; additional allauth headless endpoints are not exposed.

## Notebook access

Set NOTEBOOK_ALLOWED_HOSTS to exact allowed HTTPS hostnames.
Course owners set a course lab_url and can override a team's lab_url.
Old domain_name settings remain readable for compatibility, but every resolved URL is allowlisted.
Operators confirm each enrollment's NotebookAccess after independently granting access in DHBW.
The course management Students tab records confirmation; students see pending access until confirmed.
This confirmation is an operator assertion, not an automatic Hub provisioning or permissions check.
External/local Databrix accounts do not imply a DHBW account exists.
DHBW administrators control actual Hub identities, team sharing, kernels, and workspace recovery.
Students export saved notebooks and upload them in Databrix; there is no automatic filesystem synchronization.

Django `/admin/` is restricted to superuser inspection. Business changes use the API/UI so grades,
team constraints and immutable file history cannot be bypassed through generic model forms.
