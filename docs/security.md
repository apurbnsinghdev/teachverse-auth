### 3. `docs/security.md`
This is your **"Trust" document** for potential employers.

```markdown
# Security Overview

## Authentication
- **Protocol**: JWT (JSON Web Tokens).
- **Security**: HS256 algorithm with rotating secrets.
- **Expiration**: Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`.

## Authorization
- **Granularity**: Service-Resource-Action triplet model (e.g., `course:lesson:view`).
- **Resiliency**: Database-level permission checks with support for future Redis-based caching.