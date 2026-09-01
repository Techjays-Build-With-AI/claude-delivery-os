# Auth library registry

**Purpose.** Deterministic mapping from AUTH LIBRARY (detected by imports in an auth middleware's file) → TOKEN TYPE + CLIENT ACQUISITION PATTERN. Used by `tl-code-map` Pass B (see `extraction-guide.md § Auth-pattern extraction`) to fill the endpoint unit's `## Auth` structured fields dynamically per stack.

**This registry is EXTENSIBLE.** When you encounter a library not listed here, add a new entry — that's the intended lifecycle. Every entry is stack-agnostic in STRUCTURE (same fields for every library), stack-specific in CONTENT (each library's specific imports, code shapes, and client-side counterparts).

**Format per entry:**

```yaml
- library: <exact import path or package name>
  language: <primary language>
  ecosystem: <framework family, e.g. Node/Express, Python/FastAPI, Rails, .NET Core, Go>
  token_type: <human-readable name for this credential class>
  import_signal:                       # imports that identify this library in the auth middleware file
    - <import statement or pattern>
  verification_signature:              # function-call shape that performs the verification
    - <code snippet — regex-friendly>
  client_acquisition_pattern:          # what to grep for in the CONSUMER repo's source
    language: <consumer language if different>
    grep_for:                          # regex-friendly patterns
      - <pattern>
    canonical_call: <the one-line code the consumer must use>
  header_format: <exact header the wire carries>
  common_extracts:                     # what the middleware typically sets on the request context
    - <field name + description>
  common_env_vars:                     # env vars the library typically requires
    - <var name>: <purpose>
  common_failure_responses:            # standard failure branches this library uses
    - <condition>: <status + code + message>
```

---

## Registry — extend as new libraries are encountered

```yaml
- library: firebase-admin
  language: javascript
  ecosystem: Node
  token_type: Firebase ID token
  import_signal:
    - "import * as admin from 'firebase-admin'"
    - "const admin = require('firebase-admin')"
    - "import { getAuth } from 'firebase-admin/auth'"
  verification_signature:
    - "admin.auth().verifyIdToken(...)"
    - "getAuth().verifyIdToken(...)"
  client_acquisition_pattern:
    language: javascript
    grep_for:
      - "auth\\(\\)\\.currentUser\\.getIdToken\\("
      - "firebase\\.auth\\(\\)\\.currentUser\\.getIdToken\\("
      - "getAuth\\(\\)\\.currentUser\\?\\.getIdToken\\("
    canonical_call: "await firebase.auth().currentUser.getIdToken()"
  header_format: "Authorization: Bearer <id-token>"
  common_extracts:
    - "req.user.email (from decoded.email)"
    - "req.user.uid (from decoded.uid)"
  common_env_vars:
    - FIREBASE_SERVICE_ACCOUNT: "single-line JSON of the service account credential"
    - GOOGLE_APPLICATION_CREDENTIALS: "path to the service account file (alternative to FIREBASE_SERVICE_ACCOUNT)"
  common_failure_responses:
    - no_header: "401 { code: NO_CREDENTIAL }"
    - invalid_token: "401 { code: INVALID_CREDENTIAL }"
    - firebase_not_configured: "401 { code: FIREBASE_NOT_CONFIGURED }"

- library: jsonwebtoken
  language: javascript
  ecosystem: Node
  token_type: Opaque JWT (application-signed)
  import_signal:
    - "import jwt from 'jsonwebtoken'"
    - "const jwt = require('jsonwebtoken')"
  verification_signature:
    - "jwt.verify(...)"
  client_acquisition_pattern:
    language: javascript
    grep_for:
      - "localStorage\\.getItem\\(['\\\"]jwt|token|accessToken"       # detects the read; NOT necessarily the right pattern
      - "await\\s+axios\\.post\\(['\\\"].*/login"                     # find the token-issue endpoint
    canonical_call: "<application-defined — usually POST /auth/login → store token → send in Authorization header>"
  header_format: "Authorization: Bearer <jwt>"
  common_extracts:
    - "req.user (from decoded payload — application-defined shape)"
  common_env_vars:
    - JWT_SECRET: "signing key (HS256) — MUST be secret"
    - JWT_PUBLIC_KEY: "public key (RS256/ES256 asymmetric)"
  common_failure_responses:
    - no_header: "401 (application-defined)"
    - invalid_signature: "401 (application-defined)"
    - expired: "401 (application-defined)"

- library: passport
  language: javascript
  ecosystem: Node
  token_type: Delegated (strategy-defined)
  import_signal:
    - "import passport from 'passport'"
    - "const passport = require('passport')"
  verification_signature:
    - "passport.authenticate(<strategy-name>, ...)"
  client_acquisition_pattern:
    language: javascript
    grep_for:
      - "session|cookie|Bearer"                                        # depends on strategy configured
    canonical_call: "<strategy-defined — check the passport strategy config file for token flow>"
  header_format: "<varies by strategy — Bearer for passport-http-bearer, Cookie for session-based, etc.>"
  common_extracts:
    - "req.user (from strategy's verify callback)"
  common_env_vars:
    - "<strategy-defined — check strategy config>"

- library: next-auth
  language: javascript
  ecosystem: Node/Next.js
  token_type: next-auth session (opaque server-verified or JWT cookie)
  import_signal:
    - "import { getServerSession } from 'next-auth'"
    - "import NextAuth from 'next-auth'"
  verification_signature:
    - "getServerSession(...)"
    - "getToken({ req })"
  client_acquisition_pattern:
    language: javascript
    grep_for:
      - "useSession\\(\\)"
      - "signIn\\("
      - "getSession\\("
    canonical_call: "const { data: session } = useSession()  // session token flows automatically via cookies"
  header_format: "Cookie: next-auth.session-token=<token>  (default session strategy)"
  common_extracts:
    - "session.user.email, session.user.id (from token callback)"
  common_env_vars:
    - NEXTAUTH_SECRET: "session encryption/signing key"
    - NEXTAUTH_URL: "base URL for callback resolution"

- library: fastapi.security.OAuth2PasswordBearer
  language: python
  ecosystem: Python/FastAPI
  token_type: OAuth2 Password Bearer
  import_signal:
    - "from fastapi.security import OAuth2PasswordBearer"
    - "OAuth2PasswordBearer(tokenUrl=...)"
  verification_signature:
    - "Depends(oauth2_scheme)"
  client_acquisition_pattern:
    language: any
    grep_for:
      - "POST\\s+.*<tokenUrl-from-scheme>"                             # first, hit the token endpoint
    canonical_call: "POST /token with form-encoded username+password → response.access_token → Authorization: Bearer <access_token>"
  header_format: "Authorization: Bearer <access-token>"
  common_extracts:
    - "current_user from database lookup on decoded 'sub' claim"
  common_env_vars:
    - JWT_SECRET_KEY: "signing key"

- library: django.contrib.auth (session-based)
  language: python
  ecosystem: Python/Django
  token_type: Django session cookie
  import_signal:
    - "from django.contrib.auth.decorators import login_required"
    - "from django.contrib.auth import authenticate, login"
  verification_signature:
    - "@login_required"
    - "authenticate(request, username=..., password=...)"
  client_acquisition_pattern:
    language: any
    grep_for:
      - "POST\\s+/accounts/login/"                                     # standard Django login endpoint
    canonical_call: "POST /accounts/login/ with form data → session cookie set automatically; subsequent requests carry the cookie"
  header_format: "Cookie: sessionid=<session-key>"
  common_extracts:
    - "request.user (Django's User model)"
  common_env_vars:
    - SECRET_KEY: "Django's session encryption key"
    - DATABASE_URL: "session store (or SESSION_ENGINE setting)"

- library: djangorestframework.authentication.TokenAuthentication
  language: python
  ecosystem: Python/Django REST Framework
  token_type: DRF Token (opaque, database-backed)
  import_signal:
    - "from rest_framework.authentication import TokenAuthentication"
  verification_signature:
    - "TokenAuthentication (in authentication_classes)"
  client_acquisition_pattern:
    language: any
    grep_for:
      - "POST\\s+/api-token-auth/"
      - "POST\\s+/auth/token/"
    canonical_call: "POST /api-token-auth/ with username+password → response.token → Authorization: Token <token>"
  header_format: "Authorization: Token <token>"
  common_extracts:
    - "request.user (looked up from Token table)"

- library: spring-security
  language: java
  ecosystem: Java/Spring Boot
  token_type: Spring Security principal (mechanism-defined by SecurityFilterChain)
  import_signal:
    - "import org.springframework.security.core.Authentication"
    - "import org.springframework.security.oauth2.jwt.JwtDecoder"
    - "@PreAuthorize"
  verification_signature:
    - "SecurityContextHolder.getContext().getAuthentication()"
    - "@PreAuthorize(\"hasRole('...')\")"
  client_acquisition_pattern:
    language: any
    grep_for:
      - "<application-defined per SecurityFilterChain — check WebSecurityConfig>"
    canonical_call: "<mechanism-defined — check the application's SecurityFilterChain config>"
  header_format: "<varies — Bearer for OAuth2ResourceServer, Cookie for session, Basic for HTTP Basic>"
  common_extracts:
    - "Authentication.getPrincipal() → UserDetails"
  common_env_vars:
    - "<application-defined — check application.properties for jwk-set-uri, issuer, etc.>"

- library: microsoft.aspnetcore.identity
  language: csharp
  ecosystem: .NET Core
  token_type: ASP.NET Identity cookie OR JWT (scheme-defined)
  import_signal:
    - "using Microsoft.AspNetCore.Identity"
    - "using Microsoft.AspNetCore.Authentication.JwtBearer"
  verification_signature:
    - "[Authorize]"
    - "services.AddAuthentication(...).AddJwtBearer(...)"
  client_acquisition_pattern:
    language: any
    grep_for:
      - "<application-defined — check Program.cs / Startup.cs for scheme>"
    canonical_call: "<scheme-defined>"
  header_format: "<Cookie for Identity default; Authorization: Bearer for JWT scheme>"
  common_extracts:
    - "HttpContext.User.Identity"
    - "User.FindFirst(ClaimTypes.Email)?.Value"
  common_env_vars:
    - Jwt__Key: "JWT signing key"
    - Jwt__Issuer: "expected issuer"
    - Jwt__Audience: "expected audience"

- library: devise / warden
  language: ruby
  ecosystem: Ruby/Rails
  token_type: Devise session (cookie) OR Devise JWT
  import_signal:
    - "devise :database_authenticatable, :registerable"
    - "before_action :authenticate_user!"
  verification_signature:
    - "authenticate_user!"
    - "current_user"
  client_acquisition_pattern:
    language: any
    grep_for:
      - "POST\\s+/users/sign_in"
    canonical_call: "POST /users/sign_in with { user: { email, password } } → cookie set OR JWT in response"
  header_format: "<Cookie for standard Devise; Authorization: Bearer for devise-jwt>"
  common_extracts:
    - "current_user (Rails helper)"

- library: gorilla/sessions
  language: go
  ecosystem: Go
  token_type: Gorilla session cookie
  import_signal:
    - "import \"github.com/gorilla/sessions\""
  verification_signature:
    - "store.Get(r, \"<session-name>\")"
  client_acquisition_pattern:
    language: any
    grep_for:
      - "<application-defined login endpoint>"
    canonical_call: "POST /login → session cookie set"
  header_format: "Cookie: <session-name>=<value>"
  common_env_vars:
    - SESSION_SECRET: "session encryption/signing key"

- library: golang-jwt/jwt
  language: go
  ecosystem: Go
  token_type: Opaque JWT
  import_signal:
    - "import \"github.com/golang-jwt/jwt/v5\""
    - "import \"github.com/golang-jwt/jwt/v4\""
  verification_signature:
    - "jwt.Parse(...)"
    - "jwt.ParseWithClaims(...)"
  client_acquisition_pattern:
    language: any
    grep_for:
      - "<application-defined>"
    canonical_call: "<application-defined>"
  header_format: "Authorization: Bearer <jwt>"
  common_env_vars:
    - JWT_SECRET: "signing key"
```

---

## When you encounter a library not in the registry

1. Add a new entry with all fields filled from the library's documentation + observed code in the repo
2. Log a `DEC-###` in `shared-context/decision-log.md` recording the new entry
3. The next `/tl:code-map` run automatically uses the extended registry

## What the registry is NOT

- Not a runtime dependency — this is a static reference file the extraction procedure reads at map time
- Not an exhaustive catalogue — it grows organically as new stacks are encountered in mapped repos
- Not stack-preferential — every library gets the same fields regardless of ecosystem popularity
