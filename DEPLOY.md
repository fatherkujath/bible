# Hosting on Cloudflare Pages

The site is static: plain HTML, JavaScript and JSON files. Cloudflare Pages
watches the GitHub repository and rebuilds the site after every push, running
`scripts/build-site.sh`. A Cloudflare Access policy keeps the site private to you.

## One-time setup

### 1. Create a free Cloudflare account
Go to https://dash.cloudflare.com/sign-up and sign up with your email.

### 2. Connect the repository to Cloudflare Pages
1. In the Cloudflare dashboard, open **Workers & Pages**.
2. Choose **Create**, then the **Pages** tab, then **Connect to Git**.
3. Choose **GitHub**, sign in, and allow Cloudflare to see the `scripture-in-context`
   repository only (choose "Only select repositories").
4. Select `scripture-in-context` and choose **Begin setup**.
5. Fill in the build settings exactly:

   | Setting | Value |
   | --- | --- |
   | Project name | `scripture-in-context` (this becomes the web address) |
   | Production branch | `main` |
   | Framework preset | None |
   | Build command | `bash scripts/build-site.sh` |
   | Build output directory | `app/out` |
   | Root directory | *(leave empty)* |

6. Open **Environment variables (advanced)** and add:

   | Variable | Value |
   | --- | --- |
   | `PYTHON_VERSION` | `3.12` |
   | `NODE_VERSION` | `22` |

7. Choose **Save and Deploy**. The first build takes about 5 minutes.
   The site appears at `https://scripture-in-context.pages.dev`.

### 3. Make the site private (Cloudflare Access)
1. In the Pages project, open **Settings**, then **General**, find **Access policy**
   and choose **Enable access policy**. This protects preview links.
2. To protect the main address too: open **Zero Trust** from the dashboard sidebar
   (choose the free plan if asked; no payment needed for up to 50 users).
3. Go to **Access**, then **Applications**, then **Add an application**, then **Self-hosted**.
4. Application name: `Scripture in Context`. Application domain: `scripture-in-context.pages.dev`.
5. Add a policy: name `Only me`, action **Allow**, include **Emails**, and enter your email address.
6. Save. Opening the site now asks for your email and sends a one-time code.

## After setup
Every change pushed to `main` rebuilds and republishes automatically. A failed
build leaves the last working version online; the build log is in the Pages
project under **Deployments**.
