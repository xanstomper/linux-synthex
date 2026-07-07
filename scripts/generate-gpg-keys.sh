#!/usr/bin/env bash
# generate-gpg-keys.sh — Generate GPG keys for signing Synthex packages
# Usage: ./generate-gpg-keys.sh
set -euo pipefail

KEY_NAME="SynthOS Package Signing"
KEY_EMAIL="release@getsynthex.org"
KEY_EXPIRE="2y"
GPG_HOME="${GPG_HOME:-$HOME/.gnupg-synthex}"

echo "🔐 Generating GPG keys for Synthex package signing..."
echo "  Key name:  $KEY_NAME"
echo "  Key email: $KEY_EMAIL"
echo "  GPG home:  $GPG_HOME"
echo ""

# Generate key without user interaction
export GNUPGHOME="$GPG_HOME"
mkdir -p "$GPG_HOME"
chmod 700 "$GPG_HOME"

cat > "$GPG_HOME/batch-key" << EOF
%no-protection
Key-Type: RSA
Key-Length: 4096
Key-Usage: sign
Name-Real: $KEY_NAME
Name-Email: $KEY_EMAIL
Expire-Date: $KEY_EXPIRE
%commit
EOF

gpg --batch --generate-key "$GPG_HOME/batch-key"
rm -f "$GPG_HOME/batch-key"

# Get the key ID
KEY_ID=$(gpg --list-keys --with-colons "$KEY_EMAIL" | grep '^pub' | cut -d: -f4)
echo ""
echo "✅ GPG key generated: $KEY_ID"
echo ""

# Export public key
PUBKEY_PATH="${PUBKEY_PATH:-$GPG_HOME/RPM-GPG-KEY-synthex}"
gpg --export --armor "$KEY_ID" > "$PUBKEY_PATH"
echo "  Public key exported to: $PUBKEY_PATH"

# Export private key (for build server, keep secure!)
PRIVKEY_PATH="${PRIVKEY_PATH:-$GPG_HOME/synthex-private-key.asc}"
gpg --export-secret-keys --armor "$KEY_ID" > "$PRIVKEY_PATH"
chmod 600 "$PRIVKEY_PATH"
echo "  Private key exported to: $PRIVKEY_PATH (KEEP SECURE!)"

# Configure RPM to use this key
echo ""
echo "  Configuring RPM macros..."
mkdir -p "$HOME/.rpmmacros.d"
cat > "$HOME/.rpmmacros.d/synthex-gpg" << EOF
%_gpg_name $KEY_NAME
%__gpg_sign_cmd %{__gpg} gpg --force-v3-sigs --batch --verbose --no-armor \\
  --no-secmem-warning -u "%{_gpg_name}" -sbo %{__signature_filename} \\
  --digest-algo sha256 %{__plaintext_filename}
EOF

# Import public key into RPM database
echo "  Importing public key into RPM database..."
sudo rpm --import "$PUBKEY_PATH" 2>/dev/null || true

echo ""
echo "✅ GPG key setup complete!"
echo "  Key ID: $KEY_ID"
echo "  To sign packages: rpm --addsign package.rpm"
echo "  To verify: rpm --checksig package.rpm"
