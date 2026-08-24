# Security Policy — BLIST Ecosystem

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 11.x    | ✅ Active          |
| 10.x    | ⚠️ Security only   |
| < 10    | ❌ Unsupported     |

---

## Reporting a Vulnerability

**DO NOT** open public issues for security vulnerabilities.

### Preferred: Private Disclosure

1. **Email**: `security@blist.local` (PGP encrypted — see key below)
2. **GitHub Security Advisories**: Use "Report a vulnerability" tab in any BLIST repo
3. **Direct message**: Contact `@estiven` via secure channel

### What to Include

- Description of the vulnerability
- Steps to reproduce / PoC (if safe)
- Affected versions / components
- Potential impact assessment
- Suggested fix (if any)

### Response Timeline

| Severity | Acknowledgment | Fix Target |
| -------- | -------------- | ---------- |
| Critical | ≤ 24 hours     | ≤ 7 days   |
| High     | ≤ 48 hours     | ≤ 14 days  |
| Medium   | ≤ 72 hours     | ≤ 30 days  |
| Low      | ≤ 1 week       | Next release |

### Disclosure Process

1. **Acknowledgment** within SLA above
2. **Investigation** — we reproduce and assess
3. **Fix development** — private fork/branch
4. **Coordinated release** — patch + advisory simultaneously
5. **Credit** — you'll be credited in the advisory (unless anonymous)

---

## PGP Public Key

```
-----BEGIN PGP PUBLIC KEY BLOCK-----

mDMEZ/... (replace with actual key)

-----END PGP PUBLIC KEY BLOCK-----
```

**Fingerprint**: `XXXX XXXX XXXX XXXX XXXX  XXXX XXXX XXXX XXXX XXXX`

> **Note**: Replace the placeholder above with the actual BLIST ecosystem PGP key.
> Generate with: `gpg --full-generate-key` → `gpg --armor --export security@blist.local`

---

## Security Measures in This Repo

- ✅ **Dependabot** — weekly automated dependency updates
- ✅ **OpenSSF Scorecard** — weekly security posture scoring
- ✅ **Pinned Actions** — all GitHub Actions pinned to immutable SHAs
- ✅ **SLSA Provenance** — supply-chain integrity for releases
- ✅ **CodeQL** — static analysis on every PR (if enabled)
- ✅ **Secret Scanning** — GitHub native + custom patterns
- ✅ **Branch Protection** — required reviews, status checks, signed commits

---

## Secure Development Guidelines

### For Contributors

1. **Never commit secrets** — use GitHub Secrets / 1Password / SOPS
2. **Sign commits** — `git commit -S` (GPG/SSH)
3. **Minimal permissions** — tokens with least privilege
4. **Update dependencies** — review Dependabot PRs promptly
5. **Run locally** — `npm audit`, `npm run lighthouse`, tests before PR

### For Maintainers

1. **Review all PRs** — at least 1 approval from CODEOWNERS
2. **Verify provenance** — check SLSA attestations on releases
3. **Rotate secrets** — quarterly rotation schedule
4. **Monitor Scorecard** — address findings < 7 days
5. **Audit workflows** — quarterly review of `.github/workflows/`

---

## Incident Response

If a breach is suspected:

1. **Contain** — revoke compromised tokens, disable workflows
2. **Assess** — determine scope via logs, audit trail
3. **Notify** — GitHub Security, affected users (if data exposed)
4. **Remediate** — patch, rotate, redeploy
5. **Postmortem** — blameless, documented, shared internally

---

## Contact

- **Security Team**: `security@blist.local`
- **Maintainer**: `@estiven`
- **PGP**: See above

---

*This policy applies to all repositories under the `blistartunivers-afk` organization and personal forks used for BLIST development.*
