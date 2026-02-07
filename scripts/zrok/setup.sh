#!/bin/bash
set -e

TUNNEL_SHARE_NAME="${TUNNEL_SHARE_NAME:-my-app}"
LOCAL_PORT="${LOCAL_PORT:-3005}"
INSTALL_DIR="$HOME/.local/bin"

echo "=== zrok Setup for Groote AI ==="
echo ""

mkdir -p "$INSTALL_DIR"

TUNNEL_BIN=$(command -v zrok 2>/dev/null || echo "")
if [ -x "$INSTALL_DIR/zrok" ]; then
    TUNNEL_BIN="$INSTALL_DIR/zrok"
fi

if [ -z "$TUNNEL_BIN" ]; then
    echo "[1/4] Installing zrok..."
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64) ARCH="amd64" ;;
        aarch64|arm64) ARCH="arm64" ;;
    esac
    VERSION=$(curl -sL "https://api.github.com/repos/openziti/zrok/releases/latest" | grep '"tag_name"' | sed 's/.*"v\(.*\)".*/\1/')
    DOWNLOAD_URL="https://github.com/openziti/zrok/releases/download/v${VERSION}/zrok_${VERSION}_${OS}_${ARCH}.tar.gz"
    echo "  Downloading zrok v${VERSION} for ${OS}/${ARCH}..."
    curl -sL "$DOWNLOAD_URL" -o /tmp/zrok.tar.gz
    tar -xzf /tmp/zrok.tar.gz -C "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR/zrok"
    rm -f /tmp/zrok.tar.gz
    TUNNEL_BIN="$INSTALL_DIR/zrok"
    echo "  Installed to $INSTALL_DIR/zrok"
else
    echo "[1/4] zrok already installed ($($TUNNEL_BIN version 2>&1 | head -1))"
fi

echo ""
echo "[2/4] Account setup"
if "$TUNNEL_BIN" status &> /dev/null; then
    echo "  zrok environment already enabled"
else
    echo ""
    echo "  You need a free zrok account:"
    echo "    1. Go to https://myzrok.io and sign up"
    echo "    2. Check your email for the enable token"
    echo "    3. Run: $TUNNEL_BIN enable <TOKEN_FROM_EMAIL>"
    echo ""
    echo "  Then re-run this script: make tunnel-setup"
    exit 1
fi

echo ""
echo "[3/4] Reserving permanent share name '${TUNNEL_SHARE_NAME}'..."
RESERVE_OUTPUT=$("$TUNNEL_BIN" reserve public "http://localhost:${LOCAL_PORT}" --unique-name "$TUNNEL_SHARE_NAME" 2>&1) || true

if echo "$RESERVE_OUTPUT" | grep -q "reserved frontend endpoint"; then
    echo "  Reserved: https://${TUNNEL_SHARE_NAME}.your-tunnel-domain.example"
elif echo "$RESERVE_OUTPUT" | grep -q "already reserved"; then
    echo "  Already reserved: https://${TUNNEL_SHARE_NAME}.your-tunnel-domain.example"
else
    echo "  $RESERVE_OUTPUT"
    echo "  If the name is taken, set TUNNEL_SHARE_NAME in .env to a different name"
fi

echo ""
echo "[4/4] Configuration"
echo ""
echo "  Add to your .env file:"
echo "    PUBLIC_URL=https://${TUNNEL_SHARE_NAME}.your-tunnel-domain.example"
echo "    TUNNEL_SHARE_NAME=${TUNNEL_SHARE_NAME}"
echo ""
echo "=== Setup complete! ==="
echo ""
echo "  Start tunnel:  make tunnel-zrok"
echo "  Your URL:      https://${TUNNEL_SHARE_NAME}.your-tunnel-domain.example"
