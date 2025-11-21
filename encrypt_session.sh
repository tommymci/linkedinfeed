#!/bin/bash
# Encrypt the LinkedIn session for GitHub Actions
# Usage: ./encrypt_session.sh YOUR_ENCRYPTION_KEY

if [ -z "$1" ]; then
    echo "❌ Error: Encryption key required"
    echo "Usage: ./encrypt_session.sh YOUR_ENCRYPTION_KEY"
    echo ""
    echo "💡 Generate a secure key:"
    echo "   openssl rand -base64 32"
    exit 1
fi

ENCRYPTION_KEY="$1"

if [ ! -f "browser_state/linkedin_state.json" ]; then
    echo "❌ Error: browser_state/linkedin_state.json not found"
    echo "Please run linkedin_scraper.py first to create the session file"
    exit 1
fi

echo "🔒 Encrypting session file..."
openssl enc -aes-256-cbc -salt -pbkdf2 \
    -in browser_state/linkedin_state.json \
    -out browser_state/linkedin_state.json.enc \
    -k "$ENCRYPTION_KEY"

if [ $? -eq 0 ]; then
    echo "✅ Session encrypted successfully!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Add this as a GitHub secret named: SESSION_ENCRYPTION_KEY"
    echo "2. Go to: https://github.com/tommykhs/linkedinfeed/settings/secrets/actions"
    echo "3. Click 'New repository secret'"
    echo "4. Name: SESSION_ENCRYPTION_KEY"
    echo "5. Value: (paste your encryption key)"
    echo ""
    echo "🔒 Your encryption key (save this securely):"
    echo "$ENCRYPTION_KEY"
else
    echo "❌ Encryption failed"
    exit 1
fi
