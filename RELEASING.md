# Releasing

Releases are built by GitHub Actions ([`.github/workflows/release.yml`](.github/workflows/release.yml)). You open a release PR, push a tag, and the workflow builds the exe and installer and publishes the GitHub Release.

## Why the order matters

`docs/version.json` is what every installed copy polls for updates, and GitHub Pages serves it from `main`. If `main` gets the new `version.json` before the release assets exist, users see an update banner that links to a 404. So **tag and publish first, merge second**.

## Steps

### 1. Open a release PR

```bash
git checkout main && git pull
git checkout -b release/vX.Y.Z
```

Change these files:

| File | Change |
|---|---|
| `Python Version/version.py` | `APP_VERSION = "X.Y.Z"` |
| `CHANGELOG.md` | Rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD`, add a fresh empty `## [Unreleased]` above it, and update the compare links at the bottom |
| `docs/version.json` | `version`, `release_date`, `download_url` (`.../download/vX.Y.Z/OrbitMousePro-Setup-vX.Y.Z.exe`), `release_notes` |
| `docs/index.html` | Static fallbacks only: the download `href` and `.version-badge` text. The page refreshes them from `version.json` on load |

The installer version comes from `version.py` automatically, so `setup.iss` needs no edit.

```bash
git commit -am "Release vX.Y.Z"
git push -u origin release/vX.Y.Z
gh pr create --title "Release vX.Y.Z" --fill
```

Wait for CI to go green.

### 2. Tag the release branch and let the workflow publish

```bash
git tag -a vX.Y.Z -m "Orbit Mouse Pro vX.Y.Z"
git push origin vX.Y.Z
gh run watch    # or watch the Actions tab
```

The workflow:
1. fails if the tag doesn't match `version.py` or `CHANGELOG.md` has no matching section
2. runs the tests
3. builds the exe and installer
4. publishes the GitHub Release with the installer, a `.sha256` file, and the changelog section as notes

### 3. Smoke-test the published installer

Download it from the Release page on a Windows machine. Install it, run it, check that ENGAGE / ABORT / Stealth work, then uninstall.

### 4. Merge the release PR

Use **"Create a merge commit"**, not squash. The tagged commit must stay in `main`'s history. Pages redeploys within a minute, and installed copies see the update banner on their next launch.

## If a release build fails

Delete the tag, fix the problem on the release branch, and tag again:

```bash
git push --delete origin vX.Y.Z
git tag -d vX.Y.Z
```

## Versioning

[Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`

- **PATCH** (1.2.**1**): bug fixes only
- **MINOR** (1.**3**.0): new features, backwards compatible
- **MAJOR** (**2**.0.0): big redesigns or breaking changes

## Building locally

```bash
pip install -r "Python Version/requirements.txt" -r requirements-dev.txt
cd "Python Version"
pyinstaller --noconfirm OrbitMousePro.spec
cd ..
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DMyAppVersion=X.Y.Z installer\setup.iss
```

The installer lands in `release/OrbitMousePro-Setup-vX.Y.Z.exe`.
