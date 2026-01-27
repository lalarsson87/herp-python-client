# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please email security concerns to:

- **Email**: [security@belong.co.jp]
- **Subject**: [SECURITY] HERP-Notion Integration - [Brief Description]

Include the following information:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### What to Expect

1. **Acknowledgment**: Within 48 hours
2. **Initial Assessment**: Within 1 week
3. **Status Updates**: Weekly until resolved
4. **Resolution**: Security patches released as soon as possible

## Security Best Practices

### API Keys and Secrets

**Never commit secrets to the repository**

```bash
# Good - use environment variables
HERP_API_KEY=your-key-here

# Bad - hardcoded in code
api_key = "sk-live-abc123..."  # DON'T DO THIS
```

### Environment Variables

- Store all API keys in `.env` file
- Never commit `.env` to version control
- Use `.env.example` as template
- Rotate API keys regularly (every 90 days)

### Data Privacy

This project handles Personally Identifiable Information (PII):

- **Candidate names**
- **Email addresses**
- **Resume files**
- **Interview notes**

**Protection measures**:
- API keys with least-privilege scopes
- Encrypted data in transit (HTTPS)
- No logging of PII in plain text
- Automatic PII redaction in logs
- Secure file handling

### Code Security

**Pre-commit security checks**:
```bash
# Install pre-commit hooks
pre-commit install

# Hooks include:
# - bandit (security scanner)
# - detect-secrets (credential detection)
# - check for hardcoded credentials
```

**CI/CD security scanning**:
- Automated bandit security scans
- Credential detection in code
- Dependency vulnerability scanning

### API Security

**Rate Limiting**:
- HERP API: 100 requests/minute
- Notion API: 3 requests/second
- Automatic rate limit handling with backoff

**Error Handling**:
- Never expose API keys in error messages
- Sanitize error logs
- Use structured error classification

**Authentication**:
- API keys via environment variables only
- Never log authentication tokens
- Implement token rotation

### Dependencies

**Keep dependencies updated**:
```bash
# Check for vulnerabilities
pip-audit

# Update dependencies
pip install --upgrade -r requirements.txt
```

**Review dependency changes**:
- Check CHANGELOG before updating
- Test thoroughly after updates
- Pin critical dependencies

## Security Features

### Cache Security

**Memory-based cache**:
- No persistent storage of sensitive data
- Automatic cache expiration (TTL)
- Cache cleared on application restart

### Error Classification

**Safe error handling**:
- Automatic PII redaction
- Structured error logging
- No sensitive data in stack traces

### Batch Operations

**Rate limit protection**:
- Automatic rate limit detection
- Exponential backoff
- Request throttling

## Compliance

### Data Protection

**GDPR Compliance**:
- Right to access
- Right to deletion
- Data minimization
- Purpose limitation

**Japanese Privacy Law**:
- Comply with Act on the Protection of Personal Information (APPI)
- Proper consent for data processing
- Secure data handling

### Audit Trail

**Logging**:
- Structured logging with timestamps
- User action tracking
- API request logging (without PII)
- Error logging with sanitization

## Incident Response

### In Case of Security Breach

1. **Immediate Actions**:
   - Revoke compromised API keys
   - Notify security team
   - Document the incident

2. **Assessment**:
   - Determine scope of breach
   - Identify affected data
   - Assess impact

3. **Remediation**:
   - Apply security patches
   - Rotate all credentials
   - Update access controls

4. **Communication**:
   - Notify affected parties
   - Document lessons learned
   - Update security procedures

## Security Checklist

### For Developers

- [ ] Never commit `.env` file
- [ ] Use environment variables for secrets
- [ ] Run security scans before committing
- [ ] Review dependency vulnerabilities
- [ ] Sanitize all logs
- [ ] Use least-privilege API scopes
- [ ] Implement proper error handling
- [ ] Add security tests

### For Reviewers

- [ ] Check for hardcoded secrets
- [ ] Verify API key handling
- [ ] Review PII handling
- [ ] Check error message sanitization
- [ ] Verify rate limiting
- [ ] Review dependency changes
- [ ] Ensure security tests pass

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [Belong Inc Security Policies](https://belong.co.jp/security)

## Contact

For security concerns:
- **Email**: security@belong.co.jp
- **Emergency**: [Emergency contact information]

---

**Last Updated**: January 2026
**Next Review**: April 2026
