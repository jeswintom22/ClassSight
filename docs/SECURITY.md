# ClassSight Security Guide

**Maintainer**: Jeswin Tom (jeswintom8@gmail.com)

## 🔒 Security Overview

This document outlines the security measures implemented in ClassSight and best practices for maintaining a secure deployment. For security-related questions or to report vulnerabilities, please contact the maintainer.

## Implemented Security Features

### 1. Rate Limiting

**Purpose**: Prevents abuse and DDoS attacks

**Implementation**:
- IP-based rate limiting using SlowAPI
- Different limits for different endpoint types
- Graceful 429 responses with Retry-After headers

**Rate Limits**:
- Health/info endpoints: 60 requests/minute
- OCR analysis: 10 requests/minute (resource-intensive)
- Default endpoints: 30 requests/minute

**Configuration**: See `config.py` and `.env` for customization

### 2. Input Validation & Sanitization

**File Upload Security**:
- File extension validation (`.png`, `.jpg`, `.jpeg`, `.bmp` only)
- MIME type verification
- Magic number checking (prevents file type spoofing)
- File size limits (10 MB default)
- Filename sanitization (prevents path traversal attacks)

**Text Input Security**:
- HTML/XSS sanitization using `bleach`
- Length limits (50K characters default)
- Special character filtering
- Prompt injection prevention

**Implementation**: See `utils/validators.py`

### 3. API Key Security

**Best Practices**:
- ✅ API keys stored in `.env` file (NOT in version control)
- ✅ `.env` is in `.gitignore`
- ✅ API key validation on startup
- ✅ Clear error messages for missing/invalid keys
- ✅ No keys exposed to client-side code

**Key Rotation Procedure**:
1. Generate new API key at https://aistudio.google.com/app/apikey
2. Update `GEMINI_API_KEY` in `.env` file
3. Restart the application
4. Revoke old API key in Google AI Studio

### 4. CORS (Cross-Origin Resource Sharing)

**Development Mode**:
- Allows all origins (`CORS_ALLOW_ALL=True`)
- Suitable for local development only

**Production Mode**:
- Restrict to specific domains
- Set `CORS_ALLOW_ALL=False`
- Configure `CORS_ORIGINS` in `.env`:
  ```
  CORS_ORIGINS=https://classsight.com,https://app.classsight.com
  ```

### 5. Security Headers

**Implemented Headers**:
- `Content-Security-Policy` - Prevents XSS attacks
- `X-Frame-Options` - Prevents clickjacking (set to DENY)
- `X-Content-Type-Options` - Prevents MIME sniffing
- `Permissions-Policy` - Restricts browser features
- `X-XSS-Protection` - Legacy XSS protection
- `Referrer-Policy` - Controls referrer information

**Implementation**: See `middleware/security_headers.py`

## OWASP Top 10 Compliance

| OWASP Risk | Mitigation | Status |
|------------|-----------|--------|
| A01: Broken Access Control | Rate limiting, input validation | ✅ |
| A02: Cryptographic Failures | API keys in env vars, HTTPS ready | ✅ |
| A03: Injection | Input sanitization, parameterization | ✅ |
| A04: Insecure Design | Security-first architecture | ✅ |
| A05: Security Misconfiguration | Default secure settings, validation | ✅ |
| A06: Vulnerable Components | Regular dependency updates | ⚠️ Manual |
| A07: Auth Failures | Rate limiting (auth coming later) | 🟡 Partial |
| A08: Software/Data Integrity | Input validation, file checks | ✅ |
| A09: Logging Failures | Error logging implemented | 🟡 Partial |
| A10: SSRF | Not applicable (no external requests) | N/A |

## Security Checklist for Deployment

### Pre-Production

- [ ] Set `DEBUG=False` in `.env`
- [ ] Set `CORS_ALLOW_ALL=False`
- [ ] Configure specific `CORS_ORIGINS`
- [ ] Enable HTTPS (set up reverse proxy)
- [ ] Review and adjust rate limits
- [ ] Rotate API keys
- [ ] Review all environment variables
- [ ] Test with malicious inputs

### Production

- [ ] Use HTTPS only
- [ ] Enable `Strict-Transport-Security` header (uncomment in `security_headers.py`)
- [ ] Set up monitoring and alerting
- [ ] Regular dependency updates
- [ ] Regular security audits
- [ ] Backup API keys securely
- [ ] Monitor rate limit violations
- [ ] Review logs for suspicious activity

## Configuration Reference

### Environment Variables

See `.env.example` for all available options.

**Critical Security Settings**:
```bash
# Production settings
DEBUG=False
CORS_ALLOW_ALL=False
CORS_ORIGINS=https://yourdomain.com
RATE_LIMIT_ENABLED=True
```

## Incident Response

### API Key Compromise

1. **Immediate**: Revoke compromised key in Google AI Studio
2. Generate new API key
3. Update `.env` file with new key
4. Restart application
5. Review access logs for suspicious activity
6. Monitor for unauthorized usage

### Rate Limit Evasion

1. Review rate limit logs
2. Identify attack patterns (IP addresses, timing)
3. Consider lowering rate limits temporarily
4. Implement IP blocking if necessary
5. Consider upgrading to Redis-based rate limiting (distributed)

### File Upload Attack

1. Review uploaded file logs
2. Check for malicious content
3. Adjust file validation rules if needed
4. Clean up any suspicious temporary files

## Future Security Enhancements

- [ ] User authentication (OAuth2, JWT)
- [ ] Role-based access control (RBAC)
- [ ] Redis-based distributed rate limiting
- [ ] Automated security scanning (SAST/DAST)
- [ ] API request logging and monitoring
- [ ] Encrypted file storage
- [ ] Content fingerprinting and deduplication
- [ ] WAF (Web Application Firewall) integration

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SlowAPI Documentation](https://slowapi.readthedocs.io/)

## Contact

For security concerns or to report vulnerabilities, please contact:
- Email: security@classsight.com (update with actual contact)

---

**Last Updated**: 2026-02-14  
**Security Review**: Required quarterly
