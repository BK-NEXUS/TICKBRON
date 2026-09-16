# AUTH CONTRACT

Browser auth is session-based with secure HttpOnly/Secure/SameSite cookies. State-changing requests require CSRF protection. JWT must not be stored in localStorage. Session rotation, verification, rate limiting and RBAC are mandatory.
