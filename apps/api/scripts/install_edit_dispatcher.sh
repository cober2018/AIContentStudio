#!/bin/zsh
# Installs the auto-edit dispatcher as a launchd job (every minute, one edit at a time).
# Uninstall: launchctl bootout gui/$(id -u)/com.aicontent.edit-dispatcher && rm ~/Library/LaunchAgents/com.aicontent.edit-dispatcher.plist
set -euo pipefail
API="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.aicontent.edit-dispatcher"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOGS="$HOME/AIContentStudio/edit-logs"
mkdir -p "$LOGS"
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>$API/.venv/bin/python</string><string>$API/scripts/edit_dispatcher.py</string></array>
  <key>StartInterval</key><integer>60</integer>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string></dict>
  <key>StandardOutPath</key><string>$LOGS/dispatcher.log</string>
  <key>StandardErrorPath</key><string>$LOGS/dispatcher.log</string>
</dict></plist>
PLIST
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "installed $LABEL; logs in $LOGS"
