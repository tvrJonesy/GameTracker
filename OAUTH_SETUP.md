# GameTracker OAuth Setup Guide

GameTracker uses OAuth 2.0 to access your Google Drive. This means the app acts **as you**, using your own Drive storage — no service account, no quota issues.

## One-time setup (15 minutes)

### Step 1: Create OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or use an existing one) called "GameTracker"
3. Enable the **Google Drive API**:
   - Go to **APIs & Services → Library**
   - Search for "Google Drive API"
   - Click **Enable**

4. Create OAuth credentials:
   - Go to **APIs & Services → Credentials**
   - Click **Create Credentials → OAuth client ID**
   - If prompted, configure the OAuth consent screen:
     - User Type: **External**
     - App name: `GameTracker`
     - User support email: your email
     - Developer contact: your email
     - Scopes: leave default, click **Save and Continue**
     - Test users: add your own Google account email
     - Click **Save and Continue**, then **Back to Dashboard**

5. Create the OAuth client:
   - Click **Create Credentials → OAuth client ID** again
   - Application type: **Web application**
   - Name: `GameTracker Web App`
   - Authorized redirect URIs: Add **two** URIs:
     - `http://localhost:8501` (for local testing)
     - `https://your-username-gametracker.streamlit.app` (replace with your actual Streamlit app URL)
   - Click **Create**

6. **Download the JSON** — a popup shows your client ID and secret. Copy both.

### Step 2: Add Credentials to Streamlit Secrets

1. Open your Streamlit app dashboard
2. Go to **Settings → Secrets**
3. Add this (replace with your actual values):

```toml
gdrive_folder_id = "YOUR_DRIVE_FOLDER_ID"
colab_notebook_url = "https://colab.research.google.com/drive/YOUR_NOTEBOOK_ID"

[oauth]
client_id = "123456789-abcdef.apps.googleusercontent.com"
client_secret = "GOCSPX-your_secret_here"
redirect_uri = "https://your-username-gametracker.streamlit.app"
```

4. Click **Save**
5. Your app will restart automatically

### Step 3: First Login

1. Open your GameTracker app
2. Click **Sign in with Google**
3. Choose your Google account
4. You'll see a warning "Google hasn't verified this app" — click **Advanced → Go to GameTracker (unsafe)**
   - This is normal for apps in testing mode. You're authorizing your own app to access your own Drive.
5. Click **Allow** to grant Drive access
6. You'll be redirected back to the app — you're now signed in!

The app stores your access token in the browser session. You'll stay signed in until you close the tab.

---

## FAQ

**Q: Why does it say "Google hasn't verified this app"?**  
A: Your OAuth app is in "Testing" mode, which is fine for personal use. To remove the warning, you'd need to submit for Google's verification process (takes weeks, only needed for public apps).

**Q: Do I need to sign in every time?**  
A: Only once per browser session. If you close the tab and reopen it, you'll need to sign in again. This is more secure than storing long-lived credentials.

**Q: Can other people use my app?**  
A: Yes, but they need to sign in with their own Google account. Each user's files stay in their own Drive. If you want others to use it, add their emails to "Test users" in the OAuth consent screen.

**Q: Is this secure?**  
A: Yes — OAuth is more secure than service accounts. The app never sees your Google password, only receives a temporary access token that you can revoke at any time in your Google account settings.
