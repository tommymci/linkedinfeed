# GitHub Actions Setup Guide

Complete guide to deploy LinkedIn Feed Scraper on GitHub with automated scraping.

## 🎯 Features

- ✅ Automated scraping at **10 AM and 2 PM HKT** daily
- ✅ Manual trigger via GitHub Actions UI
- ✅ **Encrypted session storage** (public repo safe)
- ✅ Auto-deploy feeds to GitHub Pages
- ✅ Incremental scraping (only new posts)

---

## 📋 Prerequisites

1. GitHub account
2. Local scraper already working with saved session
3. Session file exists: `browser_state/linkedin_state.json`

---

## 🚀 Step-by-Step Setup

### 1. Generate Encryption Key

Generate a secure 256-bit encryption key:

```bash
openssl rand -base64 32
```

**Save this key securely!** You'll need it in step 3.

Example output:
```
Xk7Y9mP2vL3nH8jK4sF6dR1wQ5tN0zC9pA2bM7uE8vG=
```

---

### 2. Encrypt Your Session

Run the encryption script with your key:

```bash
./encrypt_session.sh "Xk7Y9mP2vL3nH8jK4sF6dR1wQ5tN0zC9pA2bM7uE8vG="
```

This creates `browser_state/linkedin_state.json.enc` (encrypted file safe for GitHub).

---

### 3. Initialize Git Repository

```bash
# Initialize repo
git init
git add .
git commit -m "Initial commit - LinkedIn Feed Scraper"

# Add remote and push
git branch -M main
git remote add origin https://github.com/tommykhs/linkedinfeed.git
git push -u origin main
```

---

### 4. Add GitHub Secret

1. Go to: https://github.com/tommykhs/linkedinfeed/settings/secrets/actions
2. Click **"New repository secret"**
3. Name: `SESSION_ENCRYPTION_KEY`
4. Value: Paste your encryption key (from step 1)
5. Click **"Add secret"**

---

### 5. Enable GitHub Pages

1. Go to: https://github.com/tommykhs/linkedinfeed/settings/pages
2. Source: **Deploy from a branch**
3. Branch: **gh-pages** / **(root)**
4. Click **Save**

Your feeds will be available at:
- https://tommykhs.github.io/linkedinfeed/master-concept.xml
- https://tommykhs.github.io/linkedinfeed/digital-action-lab.xml

---

## 🔄 How It Works

### Scheduled Runs (Automatic)

GitHub Actions runs **twice daily**:
- **10:00 AM HKT** (2:00 AM UTC)
- **2:00 PM HKT** (6:00 AM UTC)

**Process:**
1. Decrypt session file
2. Scrape Master Concept → Generate RSS
3. Scrape Digital Action Lab → Generate RSS
4. Re-encrypt session (in case cookies updated)
5. Commit feeds to `main` branch
6. Deploy to GitHub Pages (`gh-pages` branch)

### Manual Trigger

1. Go to: https://github.com/tommykhs/linkedinfeed/actions
2. Click **"Scrape LinkedIn Feeds"** workflow
3. Click **"Run workflow"** dropdown
4. Select page:
   - **both** (default) - Scrape both pages
   - **master-concept** - Only Master Concept
   - **digital-action-lab** - Only Digital Action Lab
5. Click **"Run workflow"**

---

## 🔒 Security

### Session Encryption

- **Unencrypted**: `browser_state/linkedin_state.json` (gitignored, local only)
- **Encrypted**: `browser_state/linkedin_state.json.enc` (committed to GitHub)
- **Encryption**: AES-256-CBC with PBKDF2
- **Key storage**: GitHub Secrets (encrypted at rest)

### What's Safe to Commit

✅ **Safe** (already in repo):
- Encrypted session (`.enc` file)
- Feed files (`feed/*.xml`, `feed/*.json`)
- Source code

❌ **Never commit**:
- Unencrypted session (`linkedin_state.json`)
- Encryption key (use GitHub Secrets)

---

## 📊 Monitoring

### View Workflow Runs

https://github.com/tommykhs/linkedinfeed/actions

Check for:
- ✅ Green checkmark = Success
- ❌ Red X = Failed (check logs)

### Common Issues

#### 1. Session Expired

**Error**: Login required during scraping

**Fix**:
```bash
# Re-login locally
python linkedin_scraper.py

# Re-encrypt and push
./encrypt_session.sh "YOUR_KEY"
git add browser_state/linkedin_state.json.enc
git commit -m "Update session"
git push
```

#### 2. No New Posts

**Output**: "⚠️  No NEW posts were scraped"

**This is normal!** Incremental mode found the target post.

#### 3. Workflow Failed

Check logs at: https://github.com/tommykhs/linkedinfeed/actions

Common fixes:
- Re-encrypt session (session expired)
- Check GitHub Secret is set correctly
- Verify encryption key matches

---

## 🛠 Maintenance

### Update Scraping Schedule

Edit `.github/workflows/scrape-linkedin.yml`:

```yaml
schedule:
  - cron: '0 2,6 * * *'  # Current: 10 AM, 2 PM HKT
```

Change to:
```yaml
schedule:
  - cron: '0 1,5,9 * * *'  # New: 9 AM, 1 PM, 5 PM HKT
```

### Add New LinkedIn Page

1. Update workflow file (`.github/workflows/scrape-linkedin.yml`)
2. Add new scraping step:

```yaml
- name: Scrape New Page
  run: |
    python linkedin_scraper.py "https://www.linkedin.com/company/new-page/posts/?feedView=all&sortBy=recent&viewAsMember=true"
    python generate_rss.py new-page
```

### Local Testing

Test the workflow locally before pushing:

```bash
# Scrape both pages
python linkedin_scraper.py "https://www.linkedin.com/company/master-concept/posts/?feedView=all&sortBy=recent&viewAsMember=true"
python generate_rss.py master-concept

python linkedin_scraper.py "https://www.linkedin.com/showcase/digital-action-lab/posts/?feedView=all&sortBy=recent&viewAsMember=true"
python generate_rss.py digital-action-lab

# Check output
ls -lh feed/
```

---

## 📱 Subscribe to Feeds

### Feed URLs (After GitHub Pages enabled)

- **Master Concept**: https://tommykhs.github.io/linkedinfeed/master-concept.xml
- **Digital Action Lab**: https://tommykhs.github.io/linkedinfeed/digital-action-lab.xml

### RSS Readers

Add these URLs to your favorite RSS reader:
- Feedly
- Inoreader
- NewsBlur
- NetNewsWire (macOS/iOS)
- Reeder (macOS/iOS)

---

## 🐛 Troubleshooting

### Verify Encryption/Decryption Works

```bash
# Encrypt
./encrypt_session.sh "YOUR_KEY"

# Decrypt (test)
openssl enc -aes-256-cbc -d -pbkdf2 \
  -in browser_state/linkedin_state.json.enc \
  -out browser_state/linkedin_state_test.json \
  -k "YOUR_KEY"

# Compare (should be identical)
diff browser_state/linkedin_state.json browser_state/linkedin_state_test.json

# Cleanup
rm browser_state/linkedin_state_test.json
```

### Check GitHub Secret

GitHub Secrets are hidden, but you can verify it's set:

1. Go to: https://github.com/tommykhs/linkedinfeed/settings/secrets/actions
2. Look for: `SESSION_ENCRYPTION_KEY`
3. If missing or wrong, update it

### Session Lifespan

LinkedIn sessions for automation typically last **1-8 hours**.

If scraping fails frequently:
- Session may be expiring faster
- Consider increasing scraping frequency
- Or re-login weekly

---

## 📚 Additional Resources

- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Cron Schedule**: https://crontab.guru/
- **GitHub Pages**: https://docs.github.com/en/pages

---

## ✅ Quick Checklist

- [ ] Encryption key generated
- [ ] Session encrypted
- [ ] Git repository initialized
- [ ] Code pushed to GitHub
- [ ] GitHub Secret added (`SESSION_ENCRYPTION_KEY`)
- [ ] GitHub Pages enabled
- [ ] First workflow run successful
- [ ] Feeds accessible via GitHub Pages
- [ ] Feeds added to RSS reader

---

## 🎉 You're Done!

Your LinkedIn feeds will now update automatically at 10 AM and 2 PM HKT every day!

**Manual trigger anytime**: https://github.com/tommykhs/linkedinfeed/actions
