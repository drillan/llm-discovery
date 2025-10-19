# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in llm-discovery, please report it by sending an email to the maintainers. Please do not open a public issue.

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

## Security Best Practices

### API Key Management

**DO:**
- Store API keys in environment variables
- Use `.env` files for local development (never commit them)
- Rotate API keys regularly
- Use separate API keys for different environments

**DON'T:**
- Hardcode API keys in source code
- Commit API keys to version control
- Share API keys in public channels
- Log or print API keys

### Example Secure Configuration

```bash
# .env file (add to .gitignore)
OPENAI_API_KEY="sk-..."
GOOGLE_API_KEY="AIza..."
GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

### File Permissions

Ensure credential files have appropriate permissions:

```bash
# Restrict permissions on credentials file
chmod 600 .env
chmod 600 /path/to/gcp-credentials.json
```

### Cache Directory

The cache directory may contain model metadata. While it doesn't contain API keys, ensure it has appropriate permissions:

```bash
# Default cache location
~/.cache/llm-discovery/

# Set restrictive permissions if needed
chmod 700 ~/.cache/llm-discovery/
```

## Security Features

### Current Implementation

1. **API Key Validation**
   - API keys are validated before use
   - No hardcoded credentials
   - Environment variable-based configuration

2. **Error Handling**
   - API keys are never included in error messages
   - Stack traces do not expose sensitive data
   - Authentication errors are generic to prevent information leakage

3. **File Operations**
   - Cache directory permissions are validated
   - TOML files are written with secure permissions
   - No arbitrary file path injection

4. **Data Privacy**
   - No telemetry or data collection
   - All data stays local
   - No third-party analytics

### Known Limitations

1. **Credential Storage**
   - API keys are stored in environment variables (secure)
   - GCP credentials are stored in JSON files (ensure proper permissions)

2. **Cache Files**
   - Model metadata is cached in TOML format
   - Cache files are not encrypted
   - Consider setting restrictive permissions on cache directory

3. **Network Security**
   - All API calls use HTTPS
   - Certificate validation is enabled by default
   - No proxy support (may be needed in corporate environments)

## Security Checklist for Contributors

When contributing to llm-discovery, ensure:

- [ ] No hardcoded credentials or API keys
- [ ] No sensitive data in logs or error messages
- [ ] Input validation for all user-provided data
- [ ] Proper file permission checks
- [ ] No SQL injection (N/A - no database)
- [ ] No command injection (no shell execution with user input)
- [ ] Dependencies are up to date
- [ ] No known vulnerabilities in dependencies

## Dependency Security

We regularly monitor dependencies for known vulnerabilities:

```bash
# Check for dependency vulnerabilities
pip-audit

# Update dependencies
uv sync --upgrade
```

### Current Dependencies

All dependencies are from trusted sources:
- Typer (CLI framework)
- Rich (terminal output)
- Pydantic (data validation)
- Official SDK clients (OpenAI, Google)

## Secure Development Practices

### Code Review

All changes require review before merging:
- Security-focused code review
- Dependency version verification
- Test coverage verification

### Testing

Security-relevant tests:
- API key validation tests
- Error message sanitization tests
- File permission tests
- Input validation tests

### CI/CD

GitHub Actions workflow includes:
- Dependency security checks
- Linting and type checking
- Test suite execution
- Coverage reporting

## Incident Response

In case of a security incident:

1. **Detection**: Automated alerts for dependency vulnerabilities
2. **Assessment**: Evaluate impact and severity
3. **Response**: Patch and release fix
4. **Disclosure**: Notify users if needed
5. **Post-mortem**: Document and improve

## Contact

For security concerns, please contact the maintainers privately.

---

Last updated: 2025-10-19
