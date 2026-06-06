#!/usr/bin/env bash
# 맥미니에 분신 봇을 24시간 서비스로 등록 (launchd).
# 한 번만 실행하면, 이후 부팅/로그인 때 자동으로 켜지고 죽어도 되살아남.
set -euo pipefail
cd "$(dirname "$0")"
DIR="$(pwd)"

PLIST_NAME="com.bunsin.bot.plist"
DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"

# 0) 사전 점검
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 가 없어. 먼저 설치해:  brew install python   (또는 xcode-select --install)"
  exit 1
fi
if [ ! -f ".env" ]; then
  echo "❌ .env 가 없어. 먼저:  cp .env.example .env  하고 키 채워."
  exit 1
fi

# 1) 가상환경 + 의존성 (run.sh 가 알아서 하지만, 등록 전에 미리 깔아둠)
if [ ! -d ".venv" ]; then
  echo "▶ 가상환경 + 의존성 설치…"
  python3 -m venv .venv
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet -r requirements.txt
fi

# 2) plist 생성 (경로 치환)
mkdir -p "$HOME/Library/LaunchAgents"
sed "s|__DIR__|$DIR|g" com.bunsin.bot.plist.template > "$DEST"
echo "▶ LaunchAgent 설치: $DEST"

# 3) 기존 거 있으면 내리고 다시 올림
launchctl unload "$DEST" 2>/dev/null || true
launchctl load "$DEST"

echo ""
echo "✅ 분신 봇 24시간 가동 시작."
echo "   - 로그 보기:   tail -f \"$DIR/bunsin.log\""
echo "   - 끄기:        launchctl unload \"$DEST\""
echo "   - 다시 켜기:   launchctl load \"$DEST\""
echo ""
echo "텔레그램에서 봇한테 /start 쳐서 살아있는지 확인해."
