# iOS Dev Setup

- `DevConfig.plist` controls the API base URL during development.
- If you run the API on your Mac and test in the iOS **Simulator**, keep:
  - `http://127.0.0.1:8000`
- If you run on a **physical iPhone**, change it to your Mac's LAN IP, e.g.:
  - `http://192.168.1.50:8000`

Make sure `DevConfig.plist` is added to your Xcode target's **Copy Bundle Resources**.
