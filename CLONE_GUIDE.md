# Repository Cloning Guide - Bibbi Cleaner v2.0

## Overview
This guide will help you clone and set up the Bibbi Cleaner v2.0 repository, a comprehensive data cleaning and analytics platform for Bibbi Parfum sales data management featuring AI-powered chat, email reporting, and external dashboard integration.

## Prerequisites

Before cloning this repository, ensure you have:

### Required Software
- **Git**: [Download and install Git](https://git-scm.com/downloads)
- **Node.js** (v16 or higher): [Download Node.js](https://nodejs.org/)
- **Python** (v3.8 or higher): [Download Python](https://python.org/downloads/)

### Required Accounts
- **GitHub account**: To access the repository
- **Supabase account**: For database services ([supabase.com](https://supabase.com))
- **OpenAI account**: For AI chat functionality ([platform.openai.com](https://platform.openai.com))
- **Email provider**: Gmail or other SMTP service for email reports

## Cloning Instructions

### Step 1: Clone the Repository
```bash
git clone https://github.com/TaskifaiDavid/bibbi-site.git
cd bibbi-site
```

### Step 2: Verify Directory Structure
After cloning, you should see this structure:
```
bibbi-site/
├── backend/              # Python FastAPI backend
│   ├── app/             # Main application code
│   ├── requirements.txt # Python dependencies
│   └── main.py          # Application entry point
├── frontend/            # React frontend with Vite
│   ├── src/            # React components and pages
│   ├── package.json    # Node.js dependencies
│   └── vite.config.js  # Build configuration
├── database/           # Database schemas and migrations
├── README.md          # Main documentation
├── SETUP_GUIDE.md     # Detailed setup instructions
└── CLAUDE.md          # Project workflow instructions
```

### Step 3: Check Git Status
```bash
git status
git branch
```
You should be on the `master` branch with a clean working directory.

## Post-Clone Setup

### Quick Setup Overview
1. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   ```

3. **Environment Configuration**:
   - Copy `.env.example` to `.env` in the backend directory
   - Configure your Supabase, OpenAI, and email credentials

### Detailed Setup Instructions
For complete setup instructions including:
- Database schema configuration
- API key setup
- Environment variables
- Feature testing

**📖 Read the comprehensive guides:**
- `README.md` - Overview and basic setup
- `SETUP_GUIDE.md` - Step-by-step setup with troubleshooting

## Quick Start

Once cloned and dependencies are installed:

```bash
# Terminal 1 - Start Backend
cd backend
uvicorn main:app --reload

# Terminal 2 - Start Frontend
cd frontend  
npm run dev
```

Access the application at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

## Repository Features

This repository includes:
- **Data Pipeline**: Excel file upload and intelligent cleaning
- **AI Chat**: Natural language database queries using OpenAI GPT-4
- **Email Reports**: Automated PDF/CSV/Excel report generation
- **Analytics Dashboard**: External dashboard integration (Tableau, Power BI, etc.)
- **User Authentication**: Secure multi-tenant access via Supabase

## Troubleshooting Common Clone Issues

### Permission Issues
```bash
# If you get permission errors
sudo chown -R $USER:$USER bibbi-site/
```

### Large Repository Size
This repository contains sample data files in `backend/uploads/`. If cloning is slow:
```bash
# Clone without history for faster download
git clone --depth 1 https://github.com/TaskifaiDavid/bibbi-site.git
```

### Git LFS (if applicable)
If you encounter Git LFS files:
```bash
git lfs install
git lfs pull
```

## Next Steps

After successful cloning:

1. **Follow Setup Guide**: Open `SETUP_GUIDE.md` for detailed configuration
2. **Read Documentation**: Review `README.md` for feature overview  
3. **Check Project Instructions**: See `CLAUDE.md` for development workflow
4. **Test Installation**: Run the quick start commands above

## Getting Help

If you encounter issues:
1. Check the `SETUP_GUIDE.md` troubleshooting section
2. Verify all prerequisites are properly installed
3. Ensure you have the required API keys and accounts
4. Check the console logs for specific error messages

---

**Repository URL**: https://github.com/TaskifaiDavid/bibbi-site.git  
**Project**: Bibbi Cleaner v2.0 - Data Analytics Platform