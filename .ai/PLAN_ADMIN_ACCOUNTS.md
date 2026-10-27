# Plan: add another admin from the site (needs approval)

Today the only way to get a second administrator is `createsuperuser` on the server. A form in the admin panel would be easier but it hands out the strongest rights, so it needs your decision first.

## Proposal
- `POST /api/v1/admin-panel/users/create-admin/`, allowed only for a super-admin (same `IsSuperAdmin` as creating an owner). Body: e-mail, first and last name, phone, password (min 12) and its confirmation. The account is staff, not super-admin (can use the panel, cannot create admins or owners).
- Every creation is written to the admin access log (who created whom).
- No self-promotion: nobody can change their own rights or another account's rights through this endpoint.
- Tests first: only a super-admin can call it; staff, owner, guest and anonymous get 403/401; weak or mismatching password and a used e-mail are refused; the log line is written; the new account cannot create accounts.
- Small admin panel form next to "create hotel owner".

## Decide
1. Should the new admins be staff only (proposed) or may they also be super-admins?
2. Keep `createsuperuser` as the only way to make a super-admin (proposed).
