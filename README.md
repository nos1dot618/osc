# Lakshay - Open Source Contributions

A completely static website showcasing my public open-source contributions in a single chronological timeline.

Includes:

- Pull requests
- Code reviews
- Issues
- Commits

**Contributions to `nos1dot618/*` are excluded to avoid inflating the numbers.**

## Architecture

The browser never calls the GitHub API.

```text
GitHub GraphQL API
        ↓
GitHub Actions (daily)
        ↓
collector.py
        ↓
data.json
        ↓
GitHub Pages
````

Workflows:

- `.github/workflows/update-data.yml`: updates `data.json` daily.
- `.github/workflows/pages.yml`: deploys the static site to GitHub Pages.

## Local Development

Requires Python 3.9+ and a GitHub token.

```bash
export GITHUB_TOKEN="YOUR_TOKEN"
python3 collector.py
python3 -m http.server 8000
```

Open `http://localhost:8000`.

On PowerShell:

```powershell
$env:GITHUB_TOKEN = "YOUR_TOKEN"
python3 collector.py
```

## GitHub Setup

Push the repository to GitHub:

```bash
git init
git add .
git commit -m "feat: add open source contribution timeline"
git branch -M main
git remote add origin git@github.com:YOUR-USER/YOUR-REPO.git
git push -u origin main
```

### GitHub Actions

The update workflow uses GitHub's built-in `GITHUB_TOKEN` and requires:

```yaml
permissions:
  contents: write
```

This allows it to commit updated `data.json`.

The workflow runs daily at **02:17 UTC** and can also be triggered manually from:

`Actions → Update contribution data → Run workflow`

### GitHub Pages

Go to:

`Settings → Pages → Build and deployment`

Select:

```text
Source: GitHub Actions
```

The included Pages workflow handles deployment.

## Configuration

The default username is:

```text
nos1dot618
```

Change `USERNAME` in `update-data.yml` to use another account.

For local runs:

```bash
USERNAME=some-user GITHUB_TOKEN="..." python3 collector.py
```

## Data

The collector filters out repositories owned by the configured username **before writing `data.json`**.

Commit contributions are represented by GitHub as daily repository counts, so they are displayed as e.g.:

```text
3 commits to owner/repository
```

The site itself requires no backend, database, or runtime API access.
