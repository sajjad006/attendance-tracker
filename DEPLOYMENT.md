# Deployment Guide - Attendance Tracker

This guide explains how to deploy both the frontend and backend of the Attendance Tracker application.

## Overview

- **Backend**: Django REST API deployed to **Railway** or **Render**
- **Frontend**: React/Vite app deployed to **Vercel**
- **Database**: PostgreSQL (provided by hosting platform)

---

## 🚀 Backend Deployment

### Option 1: Deploy to Railway (Recommended)

Railway offers a generous free tier with PostgreSQL support.

#### Steps:

1. **Create a Railway account** at [railway.app](https://railway.app)

2. **Install Railway CLI** (optional but helpful):
   ```bash
   npm install -g @railway/cli
   railway login
   ```

3. **Create a new project in Railway Dashboard**:
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Choose the `attendance_backend` directory

4. **Add PostgreSQL Database**:
   - In your project, click "New" → "Database" → "PostgreSQL"
   - Railway will automatically set `DATABASE_URL`

5. **Configure Environment Variables**:
   Go to your web service → Variables tab and add:
   ```
   DJANGO_SETTINGS_MODULE=attendance_backend.settings_prod
   SECRET_KEY=<generate-a-secure-random-string>
   DEBUG=False
   ALLOWED_HOSTS=<your-app-name>.railway.app
   CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
   CSRF_TRUSTED_ORIGINS=https://your-frontend.vercel.app,https://<your-app>.railway.app
   ```

6. **Deploy**:
   Railway will automatically deploy when you push to the connected branch.

7. **Create a superuser** (optional):
   ```bash
   railway run python manage.py createsuperuser
   ```

---

### Option 2: Deploy to Render

Render also offers free PostgreSQL with automatic deployments.

#### Steps:

1. **Create a Render account** at [render.com](https://render.com)

2. **Deploy using Blueprint** (easiest):
   - Go to Dashboard → "Blueprints" → "New Blueprint Instance"
   - Connect your GitHub repo
   - Render will use the `render.yaml` file to configure everything

3. **Or deploy manually**:
   - Create a new "Web Service"
   - Connect your GitHub repo
   - Set root directory to `attendance_backend`
   - Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`
   - Start command: `gunicorn attendance_backend.wsgi:application`

4. **Add PostgreSQL**:
   - Create a new PostgreSQL database in Render
   - Copy the "Internal Database URL" to your web service as `DATABASE_URL`

5. **Configure Environment Variables**:
   ```
   DJANGO_SETTINGS_MODULE=attendance_backend.settings_prod
   SECRET_KEY=<generate-a-secure-random-string>
   DEBUG=False
   ALLOWED_HOSTS=<your-app>.onrender.com
   CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
   CSRF_TRUSTED_ORIGINS=https://your-frontend.vercel.app,https://<your-app>.onrender.com
   ```

---

## 🎨 Frontend Deployment

### Deploy to Vercel (Recommended)

Vercel is optimized for React/Vite applications.

#### Steps:

1. **Create a Vercel account** at [vercel.com](https://vercel.com)

2. **Import your project**:
   - Click "Add New..." → "Project"
   - Import from GitHub
   - Select your repository

3. **Configure the project**:
   - Root Directory: `attendance-frontend`
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`

4. **Add Environment Variables**:
   Go to Settings → Environment Variables:
   ```
   VITE_API_URL=https://your-backend.railway.app/api
   ```
   
   ⚠️ **Important**: Vite requires environment variables to be prefixed with `VITE_`

5. **Deploy**:
   Click "Deploy" - Vercel will build and deploy your app.

6. **Redeploy after backend is ready**:
   Once your backend URL is known, update `VITE_API_URL` and redeploy.

---

### Alternative: Deploy to Netlify

1. **Create a Netlify account** at [netlify.com](https://netlify.com)

2. **Import from Git**:
   - "Add new site" → "Import an existing project"
   - Connect GitHub and select your repo

3. **Configure**:
   - Base directory: `attendance-frontend`
   - Build command: `npm run build`
   - Publish directory: `attendance-frontend/dist`

4. **Add `_redirects` file** for SPA routing:
   Create `attendance-frontend/public/_redirects`:
   ```
   /*    /index.html   200
   ```

5. **Add environment variable**:
   ```
   VITE_API_URL=https://your-backend.railway.app/api
   ```

---

## 🔧 Post-Deployment Configuration

### 1. Update CORS Settings

After deploying both apps, update your backend environment variables:

```
CORS_ALLOWED_ORIGINS=https://your-actual-frontend-url.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-actual-frontend-url.vercel.app,https://your-backend-url.railway.app
ALLOWED_HOSTS=your-backend-url.railway.app
```

### 2. Update Frontend API URL

In Vercel, update the environment variable:
```
VITE_API_URL=https://your-actual-backend-url.railway.app/api
```

### 3. Create Initial Data

Run these commands via Railway/Render CLI or shell:

```bash
# Create superuser
python manage.py createsuperuser

# If you have fixtures or seed data
python manage.py loaddata initial_data.json
```

---

## 🔐 Security Checklist

Before going to production:

- [ ] Generate a strong `SECRET_KEY` (use `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- [ ] Set `DEBUG=False`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set up HTTPS (automatic on Railway/Render/Vercel)
- [ ] Configure CORS to only allow your frontend domain
- [ ] Set up proper backup for your database

---

## 🐛 Troubleshooting

### CORS Errors
- Ensure `CORS_ALLOWED_ORIGINS` includes your frontend URL (with `https://`)
- Make sure there are no trailing slashes

### 500 Errors on Backend
- Check the logs in Railway/Render dashboard
- Ensure all environment variables are set
- Verify database connection

### Frontend Can't Connect to Backend
- Verify `VITE_API_URL` is set correctly
- Redeploy frontend after adding/changing environment variables
- Check browser console for errors

### Database Issues
- Ensure migrations ran: check deployment logs
- Use platform CLI to run migrations manually if needed

---

## 📝 Generating a Secret Key

Run this in Python to generate a secure secret key:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use an online generator, or run:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## 🔄 Continuous Deployment

Both Railway/Render and Vercel support automatic deployments:

- **Push to main branch** → Automatic deployment
- **Pull requests** → Preview deployments (Vercel)

Configure branch protection and required checks for production safety.
