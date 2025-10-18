# NPM Publishing Guide - @ce-dot-net/ce-ai-ace

Complete step-by-step guide to publish the ACE MCP server to npm.

## Prerequisites

### 1. Create npm Account
```bash
# If you don't have an npm account yet:
# Go to https://www.npmjs.com/signup

# Login to npm
npm login
# Enter username, password, and email
# You'll receive a verification code via email
```

### 2. Verify Login
```bash
npm whoami
# Should print your npm username
```

### 3. Check Package Name Availability
```bash
npm view @ce-dot-net/ce-ai-ace
# Should return "npm error 404 Not Found" (means it's available!)
```

## Publishing Steps

### Step 1: Prepare the Package

```bash
cd mcp-servers/ce-ai-ace

# Install dependencies
npm install

# Build TypeScript to JavaScript
npm run build

# Verify dist/ was created
ls -la dist/
```

### Step 2: Test Package Locally

```bash
# Test the package works
npm pack

# This creates: ce-dot-net-ce-ai-ace-1.0.0.tgz
# Verify contents
tar -tzf ce-dot-net-ce-ai-ace-1.0.0.tgz

# Should only include:
# - dist/**/*
# - README.md
# - LICENSE
# - package.json
# (No src/, no tsconfig.json, no node_modules/)
```

### Step 3: Test Installation

```bash
# Install locally to test
npm install -g ./ce-dot-net-ce-ai-ace-1.0.0.tgz

# Test it works
ce-ai-ace --help
# or
npx @ce-dot-net/ce-ai-ace

# Uninstall after testing
npm uninstall -g @ce-dot-net/ce-ai-ace
rm ce-dot-net-ce-ai-ace-1.0.0.tgz
```

### Step 4: Publish to npm

```bash
# Dry run first (see what will be published)
npm publish --dry-run

# Actually publish
npm publish --access public

# You should see:
# npm notice package size:  XXX kB
# npm notice unpacked size: XXX kB
# npm notice
# npm notice Publishing to https://registry.npmjs.org/
# + @ce-dot-net/ce-ai-ace@1.0.0
```

### Step 5: Verify Publication

```bash
# Check on npm
npm view @ce-dot-net/ce-ai-ace

# Test installation from npm
npx @ce-dot-net/ce-ai-ace

# Check on npmjs.com
open https://www.npmjs.com/package/@ce-dot-net/ce-ai-ace
```

## Updating the Package

### For Bug Fixes (1.0.0 → 1.0.1)
```bash
cd mcp-servers/ce-ai-ace

# Edit package.json: "version": "1.0.1"
# Or use npm version
npm version patch

# Rebuild and publish
npm run build
npm publish
```

### For New Features (1.0.0 → 1.1.0)
```bash
npm version minor
npm run build
npm publish
```

### For Breaking Changes (1.0.0 → 2.0.0)
```bash
npm version major
npm run build
npm publish
```

## Common Issues

### Issue: "You do not have permission to publish"
**Solution**: Make sure you're logged in and have access to @ce-dot-net scope
```bash
npm login
# Or create the organization on npmjs.com first
```

### Issue: "Package already exists"
**Solution**: Increment version number
```bash
npm version patch  # 1.0.0 → 1.0.1
```

### Issue: "Missing required field: repository"
**Solution**: Already added to package.json, should not occur

### Issue: Build fails
**Solution**: Check TypeScript errors
```bash
npm run build
# Fix any TypeScript errors
```

### Issue: Package too large
**Solution**: Check .npmignore is working
```bash
npm pack
tar -tzf ce-dot-net-ce-ai-ace-*.tgz
# Should NOT include src/ or node_modules/
```

## Unpublishing (if needed)

```bash
# Unpublish a specific version (within 72 hours)
npm unpublish @ce-dot-net/ce-ai-ace@1.0.0

# Unpublish entire package (use with caution!)
npm unpublish @ce-dot-net/ce-ai-ace --force
```

## After Publishing

### Update Plugin References

Edit `plugins/ace-orchestration/plugin.json`:

```json
{
  "mcpServers": {
    "ace-pattern-learning": {
      "command": "npx",
      "args": ["@ce-dot-net/ce-ai-ace"],
      "env": {
        "ACE_STORAGE_PATH": "${CLAUDE_PLUGIN_ROOT}/.ace-memory/patterns.db",
        "ACE_SIMILARITY_THRESHOLD": "0.85",
        "ACE_CONFIDENCE_HIGH": "0.70",
        "ACE_CONFIDENCE_MEDIUM": "0.30"
      }
    }
  }
}
```

### Test with Plugin

```bash
# Restart Claude Code
# MCP server will be downloaded automatically via npx
# No manual installation needed!
```

### Update Documentation

Add npm badge to main README.md:

```markdown
[![npm version](https://badge.fury.io/js/@ce-dot-net%2Fce-ai-ace.svg)](https://www.npmjs.com/package/@ce-dot-net/ce-ai-ace)
[![downloads](https://img.shields.io/npm/dm/@ce-dot-net/ce-ai-ace.svg)](https://www.npmjs.com/package/@ce-dot-net/ce-ai-ace)
```

## CI/CD (Future)

### GitHub Actions Auto-Publish

Create `.github/workflows/publish-npm.yml`:

```yaml
name: Publish to npm

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          registry-url: 'https://registry.npmjs.org'

      - name: Install dependencies
        run: |
          cd mcp-servers/ce-ai-ace
          npm install

      - name: Build
        run: |
          cd mcp-servers/ce-ai-ace
          npm run build

      - name: Publish to npm
        run: |
          cd mcp-servers/ce-ai-ace
          npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Then create npm token:
1. Go to https://www.npmjs.com/settings/YOUR_USERNAME/tokens
2. Create "Automation" token
3. Add to GitHub Secrets as `NPM_TOKEN`

## Summary Checklist

- [ ] npm account created and verified
- [ ] Logged in: `npm login`
- [ ] Package built: `npm run build`
- [ ] Local test: `npm pack` and verify contents
- [ ] Published: `npm publish --access public`
- [ ] Verified: `npm view @ce-dot-net/ce-ai-ace`
- [ ] Tested: `npx @ce-dot-net/ce-ai-ace`
- [ ] Updated plugin.json to use npm package
- [ ] Updated README with npm badges
- [ ] Committed and pushed changes

## Next Steps

After successful publish:

1. **Announce** - Share on social media, communities
2. **Document** - Add usage examples
3. **Monitor** - Watch for issues, feature requests
4. **Iterate** - Release updates based on feedback
5. **Grow** - Build community around ACE

🎉 **Congratulations! Your package is now public and reusable everywhere!**
