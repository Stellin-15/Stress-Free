# Release Checklist

Follow these steps in order every time you ship a new version.

## 1. Bump the version

Edit `Python Version/version.py`:
```python
APP_VERSION = "X.Y.Z"
```

## 2. Update the installer script

Edit `installer/setup.iss` — two lines:
```ini
AppVersion=X.Y.Z
OutputBaseFilename=OrbitMousePro-Setup-vX.Y.Z
```

## 3. Update the website

**`docs/version.json`** — all four fields:
```json
{
  "version": "X.Y.Z",
  "release_date": "YYYY-MM-DD",
  "download_url": "https://github.com/Stellin-15/Stress-Free/releases/download/vX.Y.Z/OrbitMousePro-Setup-vX.Y.Z.exe",
  "release_notes": "What changed."
}
```

**`docs/index.html`** — two places:
- The `href` on the download button (`<a class="btn-download" href="...">`)
- Both `<span class="version-badge">` tags (hero + footer)

## 4. Build the .exe

```bash
# From inside the Python Version/ folder with venv activated
../venv/Scripts/pyinstaller OrbitMousePro.spec
```

Output: `Python Version/dist/OrbitMousePro.exe`

**Test it** — double-click the exe and make sure the UI loads, movement starts/stops, and ESC works.

## 5. Build the installer

1. Open **Inno Setup Compiler**
2. File → Open → `installer/setup.iss`
3. Press **F9** to build

Output: `release/OrbitMousePro-Setup-vX.Y.Z.exe`

**Test it** — run the installer on a Windows account, verify the shortcut works, then uninstall via Add/Remove Programs.

## 6. Commit and tag

```bash
git add -A
git commit -m "Release vX.Y.Z"
git tag vX.Y.Z
git push && git push --tags
```

## 7. Publish on GitHub Releases

1. Go to your repo on GitHub → **Releases** → **Draft a new release**
2. Tag: `vX.Y.Z` (select the tag you just pushed)
3. Title: `Orbit Mouse Pro vX.Y.Z`
4. Write release notes (paste from `version.json`)
5. Drag in `release/OrbitMousePro-Setup-vX.Y.Z.exe`
6. Click **Publish release**

The download button on the website and the in-app updater will now point to the new file automatically (once the `version.json` push goes live via GitHub Pages).

---

## Versioning guide

| Change type | Example | Version bump |
|---|---|---|
| New feature | Add radius slider | `MINOR` (1.0.0 → 1.1.0) |
| Bug fix only | Fix ESC crash | `PATCH` (1.0.0 → 1.0.1) |
| Major rewrite | New UI, new movement modes | `MAJOR` (1.x.x → 2.0.0) |
