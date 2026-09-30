# @openg2p/notification

In-app notification inbox for OpenG2P UI.

Host apps render `Inbox` and pass a connection config. The package talks to the notification provider through an adapter, so application UI never imports Novu (or any other vendor SDK) directly.

Novu is the built-in provider. Other providers can be registered on `NotificationFactory`.

## Features

- Bell with unread badge and dropdown inbox
- All / Unread / Archived filters
- Mark as read, mark all as read, archive, unarchive
- Live updates over the provider WebSocket
- Pagination (20 per page)
- Localization overrides
- `useInboxSession` hook for custom UI inside `Inbox`

## Architecture

```text
Host app
   │
   ▼
Inbox / Bell / useInboxSession
   │
   ▼
NotificationFactory.create(provider, connection)
   │
   ▼
NotificationService adapter  (Novu today)
   │
   ▼
Provider SDK + API / WebSocket
```

The browser connects to the provider. OpenG2P backends do not proxy inbox REST or WebSocket traffic.

| Layer | Role |
|---|---|
| `Inbox` | Bell, panel, and session wiring |
| `NotificationFactory` | Looks up a provider by name |
| `NotificationService` | Provider-neutral inbox contract |
| `NovuNotificationService` | Novu adapter (`@novu/js`) |

The host app maps its own env or runtime config into `Inbox` `config`. `subscriber.subscriberId` is the current user. Do not render `Inbox` until `provider`, `applicationIdentifier`, and `subscriber.subscriberId` are all set.

## Development

From `notifications/client`:

```bash
npm install
npm run build
npm test
npm pack
```

| Command | What it does |
|---|---|
| `npm install` | Install dependencies |
| `npm run build` | Compile `src` to `dist` (CJS, ESM, and types) |
| `npm test` | Run the Vitest suite once |
| `npm run test:watch` | Re-run tests on file changes |
| `npm pack` | Create a tarball from `dist` for local installs |

Build before `npm pack`. The published package only includes `dist`.

Optional:

```bash
npm run lint
npm run lint:fix
npm run clean
```

## Usage

```tsx
"use client";

import { Inbox } from "@openg2p/notification";

<Inbox
  config={{
    provider: "novu",
    subscriber: { subscriberId },
    applicationIdentifier,
    backendUrl,
    socketUrl,
  }}
  localization={{
    notifications: t("notifications"),
    empty: t("no_notifications"),
  }}
/>
```

### Theme

Pass an optional `theme` object to make the inbox follow your application's branding. When omitted, the registry default palette is used (`#EABB13`, `#ED7C22`, `#F3F1F4`, `#E1E1E1`, `#A1A1A1`, `#000000`, `#FFFFFF`).

```tsx
import type { NotificationTheme } from "@openg2p/notification";

const inboxTheme: NotificationTheme = {
  accent: "#EABB13",        // badge, unread bar, primary action, focus ring
  accentHover: "#ED7C22",   // primary action hover
  surface: "#FFFFFF",       // panel and selected-tab background
  surfaceMuted: "#F3F1F4",  // tab track, hover backgrounds, secondary action
  text: "#000000",          // headings, selected labels
  textMuted: "#A1A1A1",     // timestamps, empty state, secondary labels
  border: "#E1E1E1",        // panel border and row dividers
  onAccent: "#FFFFFF",      // text on accent backgrounds (badge, primary action)
};

<Inbox config={...} theme={inboxTheme} />
```

`accentSoft` (unread row background) is computed automatically from `accent` and `surface` when not provided.

To swap providers later, implement `NotificationService` and call `NotificationFactory.register("name", Implementation)`.

## License

MPL-2.0
