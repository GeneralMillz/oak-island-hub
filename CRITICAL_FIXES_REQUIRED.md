# CRITICAL FIXES REQUIRED BEFORE GITHUB PUSH

**Status:** 🔴 NOT READY (35% deployment readiness)

## ⚠️ BLOCKER ISSUES (Must fix before GitHub push)

### 1. ❌ Lazy Map Loading - CRITICAL
**Files:** `app_public/index.html`, `app_public/app.js`
**Problem:** Map loads immediately on page load (Leaflet CSS/JS in HEAD)
**Impact:** Poor performance, loads 464MB tiles unnecessarily
**Fix:** Move Leaflet loading to activateView("map-view")

### 2. ❌ PI_MODE Missing in Frontend - CRITICAL  
**File:** `app_public/js/data.js`
**Problem:** loadSemanticData() loads 5MB without PI_MODE check
**Impact:** Memory bloat on Pi (loads 5.1MB unconditionally)
**Fix:** Add PI_MODE check at start of loadSemanticData()

### 3. ❌ No CORS Headers - CRITICAL
**File:** `api_server.py`
**Problem:** No CORS configuration
**Impact:** GitHub Pages cannot call API (cross-origin blocked)
**Fix:** Add flask-cors or manual CORS headers

### 4. ❌ No .gitignore - CRITICAL
**File:** `.gitignore` (doesn't exist)
**Problem:** Will commit venv/, __pycache__, data_raw/ (3GB+)
**Impact:** Cannot push to GitHub (too large)
**Fix:** Create .gitignore with venv, data_raw, tiles, __pycache__

### 5. ❌ 464MB Tiles Folder - CRITICAL
**File:** `app_public/tiles/`
**Problem:** 464MB exceeds GitHub limits
**Impact:** Cannot push to GitHub
**Fix:** Move to external CDN or add to .gitignore

### 6. ⚠️ Hardcoded API Path - HIGH PRIORITY
**File:** `app_public/js/chatbot.js`
**Problem:** Uses relative URL "/api/semantic/query"
**Impact:** Chatbot cannot reach Render API from GitHub Pages
**Fix:** Use window.CHATBOT_API_BASE variable

## 🗑️ CLEANUP REQUIRED

Delete these unused files:
```bash
rm app_public/researcher.js
rm app_public/semantic_explorer.js
rm app_public/test.html
rm app_public/index_test.html
rm app_public/full_dump.txt
rm -rf __pycache__
```

## 📝 NEW FILES NEEDED

1. `.gitignore` - Exclude venv, data_raw, tiles, __pycache__
2. `README.md` - Project documentation
3. `requirements.txt` - Flask==3.1.0, flask-cors==4.0.0
4. `runtime.txt` - python-3.13.5
5. `Procfile` - web: python api_server.py

## ✅ NEXT STEPS

1. Review full audit: `OAK_ISLAND_PRE_GITHUB_AUDIT.md` (970 lines)
2. Approve fixes
3. Apply P0 critical fixes (estimated 2-4 hours)
4. Test locally
5. Re-run audit
6. Push to GitHub

**After fixes:** Expected 85-90% readiness

---
See `OAK_ISLAND_PRE_GITHUB_AUDIT.md` for complete details.
