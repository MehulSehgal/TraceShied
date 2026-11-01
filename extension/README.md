# TraceShield extension (prototype)
Local-only: no network calls, no accounts, no server. Messages are read only after you tick the consent box and approve the browser permission prompt.

## Install
1. Open chrome://extensions, turn on Developer mode.
2. Click Load unpacked and choose this folder.
3. Open Instagram web (instagram.com) and a chat. Click the TraceShield icon, tick consent, click Enable, approve the prompt.
4. A TraceShield badge appears bottom right. It updates as messages appear and alerts when risk rises.

## Control
Pause stops reading. Revoke access removes the browser permission. Clear data wipes the in-memory messages.

## Known limits
- Instagram web markup changes often. Messages are found by position (right side = you, left side = other person). Test on your own account and adjust scan() in content.js if needed.
- Messages already on screen when monitoring starts have no timestamps, so the night-time signal only counts messages seen arriving live.
- Tagging is rules plus a Hinglish glossary (engine.js). No LLM is called.
