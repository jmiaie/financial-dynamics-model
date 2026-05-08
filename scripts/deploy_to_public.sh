#!/bin/bash
# Deploy Financial Dynamics Model to the public GitHub repo.
# Run this from the root of the Ominnow_private repo on your local machine.
#
# Usage:
#   chmod +x scripts/deploy_to_public.sh
#   ./scripts/deploy_to_public.sh

set -euo pipefail

PUBLIC_REPO="https://github.com/jmiaie/financial-dynamics-model.git"
SOURCE_BRANCH="claude/financial-dynamics-model-fnA1n"

echo "=== Financial Dynamics Model — Deploy to Public Repo ==="
echo ""

# Ensure we're on the right branch
current=$(git branch --show-current)
if [ "$current" != "$SOURCE_BRANCH" ]; then
    echo "Switching to $SOURCE_BRANCH..."
    git checkout "$SOURCE_BRANCH"
fi

# Pull latest
echo "Pulling latest from origin..."
git pull origin "$SOURCE_BRANCH" --ff-only

# Add public remote if not present
if ! git remote get-url public &>/dev/null; then
    echo "Adding 'public' remote: $PUBLIC_REPO"
    git remote add public "$PUBLIC_REPO"
fi

# Push to public main
echo ""
echo "Pushing to public repo (main branch)..."
git push public "${SOURCE_BRANCH}:main" --force

echo ""
echo "=== Done! ==="
echo "Public repo updated: $PUBLIC_REPO"
echo ""
echo "Next steps:"
echo "  1. Go to https://share.streamlit.io"
echo "  2. Deploy jmiaie/financial-dynamics-model (branch: main, file: app.py)"
echo "  3. In Porkbun DNS for micapai.com, add URL Forward:"
echo "     Subdomain: fdm"
echo "     Destination: https://financial-dynamics-model.streamlit.app"
echo "     Type: 302 Temporary"
echo ""
echo "Result: fdm.micapai.com → live dashboard"
