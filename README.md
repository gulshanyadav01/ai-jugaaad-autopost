# @ai.jugaaad auto-poster

Posts one Reel at **12:27, 18:27 and 21:27 IST** every day, using Instagram's official API.
Each run takes the next unposted Reel from `queue.json`, posts it with its caption and music,
adds the prompt as a comment, and saves progress back to the repo.

## One-time setup (about 30 minutes)

### 1. Turn on GitHub Pages (hosts the videos so Instagram can fetch them)
Repo **Settings → Pages → Build and deployment**: Source = *Deploy from a branch*,
Branch = `main`, folder = `/docs`. Save. After a minute, this should play:
`https://<your-github-username>.github.io/<repo-name>/reels/AIJugaad_Reel02_salary_negotiation.mp4`

### 2. Create the Meta app and get an Instagram token
1. Go to **developers.facebook.com → My Apps → Create app**. Use case: *Manage messaging & content on Instagram*.
2. In the app, open **Instagram → API setup with Instagram business login**.
3. Under *Generate access tokens*, click **Add account** and log in as **@ai.jugaaad**
   (it must be a Creator or Business account).
4. Make sure these permissions are granted: `instagram_business_basic`,
   `instagram_business_content_publish`, `instagram_business_manage_comments`.
5. Click **Generate token** and copy it. This is a long-lived token (valid 60 days).
   Never paste it in a chat, a file, or a commit.

While the app is in development mode, it can post to accounts that are added as testers/owners
of the app (which @ai.jugaaad is, after step 3). You do not need App Review for your own account.

### 3. Add the token to GitHub
Repo **Settings → Secrets and variables → Actions → New repository secret**
- Name: `IG_ACCESS_TOKEN`, value: the token from step 2.

Optional, for automatic token renewal every Monday:
- Create a fine-grained GitHub token (github.com/settings/personal-access-tokens) for this repo
  only, with **Secrets: Read and write**. Save it as a secret named `GH_PAT`.
- Without it, generate a fresh token in the Meta app and replace `IG_ACCESS_TOKEN` every ~55 days.

### 4. Test, then go live
- **Actions → Post next Reel → Run workflow** with *Dry run* ticked.
  It checks the token, the quota and the video link, and posts nothing.
- When the dry run is green, the schedule takes over automatically.
  To post immediately, run it again with *Dry run* unticked.

## Day to day
- **Change the order or skip a Reel:** edit `queue.json` (`"posted": true` skips it).
- **Add new Reels:** put the MP4 in `docs/reels/` and add an entry to `queue.json`.
- **Pause:** Actions → Post next Reel → ⋯ → Disable workflow.
- **Still manual:** pinning the prompt comment and replying to comments. ManyChat handles keyword DMs.

## Notes
- Music is an original lo-fi track generated for this page, so there are no copyright issues.
  API posts can't use Instagram's trending-audio library.
- Instagram allows up to 100 API posts per 24 hours; this uses 3.
