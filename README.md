# Daily Content Workflow

Automated daily pipeline that publishes 3 Blogger posts and schedules 5 Pinterest pins via Buffer every day at 11:30 UTC (5:00 PM IST).

## Setup

### 1. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions** in your GitHub repository and add these four secrets:

| Secret | Description |
|---|---|
| `GOOGLE_CLIENT_ID` | OAuth 2.0 client ID from Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 client secret from Google Cloud Console |
| `BLOGGER_REFRESH_TOKEN` | Long-lived refresh token with Blogger API scope |
| `BUFFER_TOKEN` | Buffer API Bearer token |

### 2. Enable the Blogger API

In Google Cloud Console, enable the **Blogger API v3** for the project that owns your OAuth credentials. Ensure the refresh token was obtained with the `https://www.googleapis.com/auth/blogger` scope.

### 3. Push the files

Commit and push all files to your repository. The workflow will run automatically each day at 11:30 UTC, or you can trigger it manually from the **Actions** tab using "Run workflow".

## How it works

1. Picks 3 study topics based on `day_of_month % 10`
2. Fetches a Blogger OAuth access token via the refresh token grant
3. Creates 3 blog posts via the Blogger REST API v3
4. Generates 5 Pinterest pin images (1000×1500 px) using Pillow
5. Uploads each image to tmpfiles.org to get a public URL
6. Schedules 5 Buffer pins on your Pinterest channel, staggered from 11:30–11:50 UTC
