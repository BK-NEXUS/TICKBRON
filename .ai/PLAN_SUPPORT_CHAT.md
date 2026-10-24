# Plan: chat with the TICKBRON team (2026-10-23)

Why: guests and hotel owners had no way to reach the admin through the site (the "Contact Us" page is text only, owners cannot even ask for advertising). Owner's choice: a chat on the site.

## What
- One support thread per account (guest or hotel owner). Only logged-in users can write (no anonymous chat: no spam and the team knows who is asking). The Contact page links to the chat and asks anonymous visitors to log in.
- Admin panel: a "Support chat" tab: inbox (unread first, search by name or e-mail), the thread, a reply box, an unread badge on the tab. Staff and super-admin can both answer (read and reply are staff features; no money or data changes here).
- "Real time" = short polling: every 4 s while the chat is open and the tab is visible, nothing while it is hidden, a refresh the moment the tab comes back, back-off after errors. Reason: no WebSocket server (Channels/ASGI) exists in the deployment plan; this works with the current setup. A WebSocket can replace the polling later without changing the message API.
- Unread badge for users (header menu, owner panel) is read every 30 s.
- Owner shortcut "Request advertising" fills the message box with a template (the admin then creates the ad in Advertising).

## Rules (backend, `chat/service.py`)
- Text: 1 to 2000 characters, plain text (same check as other free text: no `<`/`>`, no control characters).
- Limits per user: 20 messages a minute; polling 90 requests a minute (the default 1000 an hour would be used up by polling alone).
- A user sees only their own thread; staff see all threads. Messages are never edited or deleted by users.
- Unread = messages of the other side after the last read mark (one mark per side, shared by all staff).

## Not done
- Anonymous chat, attachments, typing indicator, push or e-mail notices (no SMTP yet), closing or assigning threads, WebSocket.
- Audit log rows for staff opening a thread (the messages are what the user wrote to the team on purpose).
