# LinkedIn Feed Scraper - Quick Usage Guide

## 📋 Adding New Pages to Scrape

**Easy!** Just edit `pages_config.json`:

```json
{
  "pages": [
    {
      "slug": "master-concept",
      "url": "https://www.linkedin.com/company/master-concept/posts/?feedView=all&sortBy=recent&viewAsMember=true",
      "name": "Master Concept"
    },
    {
      "slug": "your-new-page",
      "url": "https://www.linkedin.com/company/your-new-page/posts/?feedView=all&sortBy=recent&viewAsMember=true",
      "name": "Your New Page"
    }
  ]
}
```

Then commit and push:
```bash
git add pages_config.json
git commit -m "Add new page: your-new-page"
git push
```

**That's it!** The scheduled workflow will automatically scrape it at 10 AM and 2 PM HKT.

---

## 🔄 Refreshing Login Session

When your LinkedIn session expires (GitHub Actions fails with login error):

### Method 1: Quick Script (Recommended)

```bash
./refresh_session.sh "YOUR_ENCRYPTION_KEY"
```

Or with environment variable:
```bash
SESSION_ENCRYPTION_KEY="your_key" ./refresh_session.sh
```

**What it does:**
1. Opens browser for you to log in
2. Scrapes first page to update session
3. Re-encrypts session file
4. Commits and pushes to GitHub

### Method 2: Manual Steps

```bash
# 1. Run scraper locally (browser opens)
python3 linkedin_scraper.py

# 2. Log in to LinkedIn when prompted

# 3. Re-encrypt session
./encrypt_session.sh "YOUR_ENCRYPTION_KEY"

# 4. Commit and push
git add browser_state/linkedin_state.json.enc
git commit -m "Update LinkedIn session"
git push
```

---

## 🚀 Running Scraper Locally

### Scrape all pages from config:
```bash
python3 scrape_all.py all
```

### Scrape specific page:
```bash
python3 scrape_all.py master-concept
python3 scrape_all.py digital-action-lab
python3 scrape_all.py finda-cloud
```

### Scrape single page directly:
```bash
python3 linkedin_scraper.py "https://www.linkedin.com/company/master-concept/posts/"
python3 generate_rss.py master-concept
```

---

## ⏰ GitHub Actions Schedule

**Automatic runs:** 10 AM and 2 PM HKT daily (2 AM and 6 AM UTC)

**Manual trigger:** https://github.com/tommykhs/linkedinfeed/actions

Select page to scrape:
- **all** - Scrapes all pages in config (default)
- **master-concept** - Only Master Concept
- **digital-action-lab** - Only Digital Action Lab
- **finda-cloud** - Only Finda Cloud

---

## 📱 RSS Feed URLs

After GitHub Pages is enabled, your feeds are at:

```
https://tommykhs.github.io/linkedinfeed/feed/master-concept.xml
https://tommykhs.github.io/linkedinfeed/feed/digital-action-lab.xml
https://tommykhs.github.io/linkedinfeed/feed/finda-cloud.xml
```

**Pattern:** `https://tommykhs.github.io/linkedinfeed/feed/{slug}.xml`

---

## 🛠 Troubleshooting

### Session expired
Run: `./refresh_session.sh "YOUR_KEY"`

### Add new page
Edit: [pages_config.json](pages_config.json) and commit

### Change schedule time
Edit: [.github/workflows/scrape-linkedin.yml](.github/workflows/scrape-linkedin.yml) line 6
```yaml
- cron: '0 2,6 * * *'  # 10 AM and 2 PM HKT
```

### Test locally before pushing
```bash
python3 scrape_all.py all
```

---

## 🔑 Encryption Key

**Important:** Never commit your encryption key!

Store it securely:
- GitHub Secret: `SESSION_ENCRYPTION_KEY`
- Local: Use password manager or `.env` file (gitignored)

**Lost your key?**
1. Generate new key: `openssl rand -base64 32`
2. Update GitHub Secret
3. Re-encrypt session: `./refresh_session.sh "NEW_KEY"`

---

## 📂 File Structure

```
LinkedinFeed/
├── pages_config.json           # ⭐ Edit this to add pages
├── scrape_all.py              # Wrapper script (reads config)
├── refresh_session.sh         # ⭐ Run this to refresh login
├── linkedin_scraper.py        # Core scraper
├── generate_rss.py            # RSS generator
├── feed/                      # Generated feeds
│   ├── master-concept.xml
│   ├── digital-action-lab.xml
│   └── finda-cloud.xml
└── browser_state/
    └── linkedin_state.json.enc  # Encrypted session
```

---

## ✅ Quick Checklist

**Adding a new page:**
- [ ] Edit `pages_config.json`
- [ ] Commit and push
- [ ] Done! Workflow will pick it up

**Session expired:**
- [ ] Run `./refresh_session.sh "KEY"`
- [ ] Log in when browser opens
- [ ] Script handles the rest

**Testing locally:**
- [ ] Run `python3 scrape_all.py all`
- [ ] Check `feed/` folder for output

---

## 💡 Pro Tips

1. **Local testing:** Always test with `python3 scrape_all.py all` before pushing
2. **Session refresh:** Run `refresh_session.sh` weekly to avoid expiration
3. **Monitor runs:** Check https://github.com/tommykhs/linkedinfeed/actions regularly
4. **Incremental scraping:** Subsequent runs only fetch new posts (fast!)

---

**Need help?** Check the main [README.md](README.md) or [GITHUB_SETUP.md](GITHUB_SETUP.md)
