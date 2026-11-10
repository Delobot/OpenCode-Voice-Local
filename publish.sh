#!/usr/bin/env bash
# One-shot publisher for OpenCode Voice Local.
#
# Creates the public GitHub repository (if it does not exist yet) and pushes
# `main`. The personal access token is typed in, used for this run only, and
# never written to disk, git config or the git remote.
#
# Usage:  ./publish.sh            # repo name defaults to opencode-voice-local
#         REPO_NAME=other ./publish.sh
set -euo pipefail

REPO_NAME="${REPO_NAME:-opencode-voice-local}"
API="https://api.github.com"

cd "$(dirname "${BASH_SOURCE[0]}")"

read -rsp "GitHub token (classic with 'repo' scope, or fine-grained with repo create+push): " TOKEN
echo
[ -n "$TOKEN" ] || { echo "empty token" >&2; exit 1; }

user=$(curl -fsS -H "Authorization: Bearer $TOKEN" "$API/user" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["login"])')
echo "user: $user"

tmp=$(mktemp)
code=$(curl -s -o "$tmp" -w '%{http_code}' -X POST "$API/user/repos" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"$REPO_NAME\",\"private\":false,\"description\":\"OpenCode Voice Local: offline Russian TTS for OpenCode Desktop (Silero + Piper), settings page and compact player\"}")
case "$code" in
  201) echo "repository created: $user/$REPO_NAME" ;;
  422) echo "repository already exists: $user/$REPO_NAME" ;;
  *) echo "GitHub API error ($code):" >&2; cat "$tmp" >&2; rm -f "$tmp"; exit 1 ;;
esac
rm -f "$tmp"

git config user.name "$user"
git config user.email "$user@users.noreply.github.com"

if grep -q 'github.com/<user>/' README.md; then
  sed -i "s|github.com/<user>/|github.com/$user/|g" README.md
  git add README.md
fi

git commit --amend --reset-author --no-edit -q

git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$user/$REPO_NAME.git"

# Authenticate this single push without persisting the token anywhere.
B64=$(printf 'x-access-token:%s' "$TOKEN" | base64 -w0)
git -c http.extraHeader="Authorization: Basic $B64" push -u origin main

echo
echo "done: https://github.com/$user/$REPO_NAME"
