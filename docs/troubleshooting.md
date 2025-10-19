---
title: Troubleshooting
description: Common issues, error messages, and solutions
---

# Troubleshooting

Solutions for common issues and error messages.

## Authentication Errors

### OpenAI Authentication Failed

**Error Message**:
```
Error: Failed to fetch models from OpenAI API.
Provider: openai
Cause: AuthenticationError - Incorrect API key provided
```

**Causes**:
1. API key not set
2. API key invalid or expired
3. API key has incorrect format

**Solutions**:

1. **Verify API key is set**:
   ```bash
   echo $OPENAI_API_KEY
   ```

   If empty, set it:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

2. **Verify API key format**:
   - OpenAI keys start with `sk-`
   - Length: 51 characters
   - Example: `sk-proj-...` (project keys)

3. **Test API key manually**:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

4. **Generate new API key**:
   - Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
   - Create new key
   - Replace old key in environment

:::{warning}
API keys are sensitive credentials.
Never share API keys in logs, error messages, or version control.
:::

### Google AI Studio Authentication Failed

**Error Message**:
```
Error: Failed to fetch models from Google API.
Provider: google
Cause: AuthenticationError - API key not valid
```

**Solutions**:

1. **Verify API key is set**:
   ```bash
   echo $GOOGLE_API_KEY
   ```

2. **Verify API key format**:
   - Google AI Studio keys start with `AIza`
   - Length: 39 characters

3. **Generate new API key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create new API key
   - Set environment variable:
     ```bash
     export GOOGLE_API_KEY="AIza..."
     ```

### Vertex AI Authentication Failed

**Error Message**:
```
Error: Vertex AI authentication failed.

GOOGLE_GENAI_USE_VERTEXAI is set to 'true', but GOOGLE_APPLICATION_CREDENTIALS is not set.
```

**Solutions**:

1. **Verify Vertex AI configuration**:
   ```bash
   echo $GOOGLE_GENAI_USE_VERTEXAI
   echo $GOOGLE_APPLICATION_CREDENTIALS
   ```

2. **Set up service account**:
   ```bash
   # Create service account
   gcloud iam service-accounts create llm-discovery-sa \
     --display-name="LLM Discovery"

   # Grant permissions
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:llm-discovery-sa@PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"

   # Download key
   gcloud iam service-accounts keys create ~/gcp-key.json \
     --iam-account=llm-discovery-sa@PROJECT_ID.iam.gserviceaccount.com
   ```

3. **Set environment variables**:
   ```bash
   export GOOGLE_GENAI_USE_VERTEXAI=true
   export GOOGLE_APPLICATION_CREDENTIALS="$HOME/gcp-key.json"
   ```

4. **Verify setup**:
   ```bash
   gcloud auth application-default print-access-token
   ```

## Network Errors

### Connection Timeout

**Error Message**:
```
Error: Failed to fetch models from OpenAI API.
Cause: Connection timeout (10 seconds)
```

**Causes**:
1. Internet connection issues
2. Provider service downtime
3. Firewall blocking API requests
4. Proxy configuration issues

**Solutions**:

1. **Check internet connection**:
   ```bash
   ping 8.8.8.8
   ```

2. **Check provider status**:
   - OpenAI: https://status.openai.com/
   - Google: https://status.cloud.google.com/

3. **Test API endpoint directly**:
   ```bash
   curl -I https://api.openai.com/v1/models
   ```

4. **Configure proxy (if needed)**:
   ```bash
   export HTTP_PROXY="http://proxy.example.com:8080"
   export HTTPS_PROXY="http://proxy.example.com:8080"
   ```

5. **Increase timeout (not recommended)**:
   - Default: 10 seconds
   - Consider network issues if timeout needed

### DNS Resolution Failed

**Error Message**:
```
Error: Failed to fetch models from OpenAI API.
Cause: Name or service not known
```

**Solutions**:

1. **Check DNS resolution**:
   ```bash
   nslookup api.openai.com
   ```

2. **Try alternative DNS**:
   ```bash
   # Temporarily use Google DNS
   export DNS_SERVER="8.8.8.8"
   ```

3. **Check /etc/hosts**:
   ```bash
   cat /etc/hosts | grep openai
   ```

   Remove any incorrect entries.

## Rate Limit Errors

### Rate Limit Exceeded

**Error Message**:
```
Error: Failed to fetch models from OpenAI API.
Cause: Rate limit exceeded (429 Too Many Requests)
```

**Causes**:
1. Too many requests in short time period
2. API key tier limits reached
3. Concurrent requests exceeding limit

**Solutions**:

1. **Wait and retry**:
   ```bash
   # Wait 60 seconds
   sleep 60
   llm-discovery update
   ```

2. **Implement retry logic** (Python API):
   ```python
   import asyncio
   import time
   from llm_discovery import DiscoveryClient
   from llm_discovery.exceptions import ProviderFetchError

   async def fetch_with_retry():
       client = DiscoveryClient()
       max_retries = 3
       base_delay = 60  # seconds

       for attempt in range(max_retries):
           try:
               return await client.fetch_models()
           except ProviderFetchError as e:
               if "429" in str(e) and attempt < max_retries - 1:
                   delay = base_delay * (2 ** attempt)
                   print(f"Rate limited. Retrying in {delay}s...")
                   time.sleep(delay)
               else:
                   raise

   asyncio.run(fetch_with_retry())
   ```

3. **Reduce request frequency**:
   - Use caching to minimize API calls
   - Schedule updates every 6-24 hours (not minutes)

4. **Check API key tier limits**:
   - OpenAI: Check usage dashboard
   - Google: Check quotas in console

:::{important}
Rate limits are enforced by providers to ensure fair usage.
Respect rate limits to avoid API key suspension.
:::

## Cache-Related Issues

### Cache Not Found

**Error Message**:
```
Error: Cache file not found.

Location: ~/.cache/llm-discovery/models.toml

Please run the update command first to fetch models from APIs:
  llm-discovery update
```

**Solutions**:

1. **Run update command**:
   ```bash
   llm-discovery update
   ```

2. **Verify cache location**:
   ```bash
   ls -la ~/.cache/llm-discovery/
   ```

3. **Check custom cache directory** (if set):
   ```bash
   echo $LLM_DISCOVERY_CACHE_DIR
   ls -la $LLM_DISCOVERY_CACHE_DIR
   ```

### Cache Corrupted

**Error Message**:
```
Error: Cache file is corrupted.

Location: ~/.cache/llm-discovery/models.toml
Cause: TOML parse error at line 15
```

**Causes**:
1. Incomplete write (process interrupted)
2. File system corruption
3. Manual file editing

**Solutions**:

1. **Clear cache and refetch**:
   ```bash
   rm -rf ~/.cache/llm-discovery/
   llm-discovery update
   ```

2. **Backup and investigate**:
   ```bash
   cp -r ~/.cache/llm-discovery/ ~/llm-discovery-backup/
   cat ~/.cache/llm-discovery/models.toml | head -20
   ```

3. **Check file permissions**:
   ```bash
   ls -la ~/.cache/llm-discovery/models.toml
   chmod 644 ~/.cache/llm-discovery/models.toml
   ```

### Cache Directory Permission Denied

**Error Message**:
```
Error: Permission denied

Location: ~/.cache/llm-discovery/
Cause: Cannot create cache directory
```

**Solutions**:

1. **Fix permissions**:
   ```bash
   mkdir -p ~/.cache/llm-discovery
   chmod 755 ~/.cache/llm-discovery
   ```

2. **Use custom cache directory**:
   ```bash
   export LLM_DISCOVERY_CACHE_DIR="/tmp/llm-discovery"
   mkdir -p $LLM_DISCOVERY_CACHE_DIR
   llm-discovery update
   ```

## Configuration Errors

### Required Environment Variable Not Set

**Error Message**:
```
Error: Required environment variable not set: OPENAI_API_KEY

At least one provider API key must be configured.
```

**Solutions**:

1. **Set at least one provider API key**:
   ```bash
   export OPENAI_API_KEY="sk-..."
   # OR
   export GOOGLE_API_KEY="AIza..."
   ```

2. **Verify environment**:
   ```bash
   env | grep -E "(OPENAI|GOOGLE)_API_KEY"
   ```

3. **Add to shell profile** (persistent):
   ```bash
   echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
   source ~/.bashrc
   ```

### Invalid Environment Variable Value

**Error Message**:
```
Error: Invalid value for GOOGLE_GENAI_USE_VERTEXAI

Expected: 'true' or 'false'
Received: 'yes'
```

**Solutions**:

1. **Use correct boolean values**:
   ```bash
   export GOOGLE_GENAI_USE_VERTEXAI=true   # Not 'yes', '1', 'True'
   export GOOGLE_GENAI_USE_VERTEXAI=false  # Not 'no', '0', 'False'
   ```

2. **Unset if not needed**:
   ```bash
   unset GOOGLE_GENAI_USE_VERTEXAI
   ```

## Export Errors

### Invalid Export Format

**Error Message**:
```
Error: Invalid export format: 'xml'

Supported formats:
  - json
  - csv
  - yaml
  - markdown
  - toml
```

**Solutions**:

1. **Use supported format**:
   ```bash
   llm-discovery export --format json --output models.json
   ```

2. **List available formats**:
   ```bash
   llm-discovery export --help
   ```

### Permission Denied Writing Output File

**Error Message**:
```
Error: Permission denied

Cannot write to: /root/models.json
```

**Solutions**:

1. **Check directory permissions**:
   ```bash
   ls -la /root/
   ```

2. **Use writable location**:
   ```bash
   llm-discovery export --format json --output ~/models.json
   # OR
   llm-discovery export --format json --output /tmp/models.json
   ```

3. **Fix permissions**:
   ```bash
   sudo chown $USER:$USER /path/to/output/directory
   ```

## Version Issues

### Package Version Not Found

**Error Message**:
```
Error: Could not retrieve package version.
This may indicate an improper installation.
```

**Causes**:
1. Editable installation without pyproject.toml
2. Package not properly installed
3. Package metadata corruption

**Solutions**:

1. **Reinstall package**:
   ```bash
   pip uninstall llm-discovery
   pip install llm-discovery
   ```

2. **Verify installation**:
   ```bash
   pip show llm-discovery
   ```

3. **For editable installation**:
   ```bash
   pip install -e . --force-reinstall
   ```

## Debugging Tips

### Enable Verbose Logging

```bash
export PYTHONLOGLEVEL=DEBUG
llm-discovery update
```

### Check System Information

```bash
# Python version
python --version

# Package version
llm-discovery --version

# Environment variables
env | grep -E "(OPENAI|GOOGLE|LLM_DISCOVERY)"

# Cache contents
ls -la ~/.cache/llm-discovery/

# Network connectivity
curl -I https://api.openai.com/v1/models
```

### Collect Diagnostic Information

```bash
# Create diagnostic report
cat > diagnostic-report.txt <<EOF
Date: $(date)
Python: $(python --version)
llm-discovery: $(llm-discovery --version 2>&1)

Environment:
$(env | grep -E "(OPENAI|GOOGLE|LLM_DISCOVERY)" | sed 's/=.*/=***/')

Cache:
$(ls -la ~/.cache/llm-discovery/ 2>&1)

Network:
$(curl -I https://api.openai.com/v1/models 2>&1 | head -5)
EOF

cat diagnostic-report.txt
```

## FAQ

### How often should I run `update`?

**Recommendation**: Every 6-24 hours

Model availability changes infrequently. Running `update` too frequently wastes API quota and may trigger rate limits.

### Can I use llm-discovery offline?

**Yes**, after initial `update`:

```bash
# Fetch once (online)
llm-discovery update

# Use offline
llm-discovery list           # Works offline
llm-discovery export         # Works offline
```

### How do I clear all cache data?

```bash
rm -rf ~/.cache/llm-discovery/
```

Then run `llm-discovery update` to rebuild cache.

### Where are API keys stored?

API keys are **never** stored by llm-discovery. They must be provided via environment variables for each session.

### How do I report a bug?

1. Check this troubleshooting guide first
2. Search existing issues on GitHub
3. Create new issue with:
   - Error message
   - Steps to reproduce
   - Diagnostic report (see above)

## Getting Help

If this guide doesn't resolve your issue:

1. **Check documentation**:
   - [API Reference](api-reference.md)
   - [CLI Reference](cli-reference.md)
   - [Advanced Usage](advanced-usage.md)

2. **Search GitHub Issues**:
   - Existing solutions may be documented

3. **Create GitHub Issue**:
   - Include diagnostic information
   - Describe steps to reproduce
   - Attach relevant logs

4. **Security Issues**:
   - Do not post security issues publicly
   - Email security concerns to project maintainers
