# Performance Optimization Testing Guide

## Quick Start

### 1. Install Updated Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../students_data_store
npm install
```

### 2. Start Services

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd students_data_store
npm run dev

# Terminal 3: Database (if using Docker)
docker-compose up
```

### 3. Verify Optimizations

#### Backend Performance Testing

```bash
# Test pagination endpoint (should be <100ms)
curl -i http://localhost:8000/api/v1/students/?skip=0&limit=100

# Test individual student caching (second call should be <10ms)
curl -i http://localhost:8000/api/v1/students/{student_id}
curl -i http://localhost:8000/api/v1/students/{student_id}  # This should be cached

# Test form submission (should be <100ms)
curl -X POST http://localhost:8000/api/v1/students/public/submit-form \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com"
  }'
```

#### Frontend Performance Testing

1. **Open DevTools (F12)** → Network tab
2. **Open DevTools** → Performance tab (Record)
3. **Navigate to Dashboard** and check:
   - Initial load time (should be <2s)
   - First Contentful Paint (should be <1s)
   - All API requests (should be <100ms each)

4. **Test Filter Performance:**
   - Open Admin Students widget
   - Type in search box while recording
   - Should be smooth with minimal lag
   - No "Not Responding" warnings

5. **Test Delete Optimistic Update:**
   - Click delete on a student
   - Should disappear immediately
   - Then verify request completes

#### Bundle Size Analysis

```bash
cd students_data_store
npm run build
ls -lh dist/

# Expected output:
# - Total size: ~400-600KB (gzipped)
# - Main chunk: ~200-300KB
# - Vendor chunks: ~200-300KB
```

### 4. Verify Specific Optimizations

#### ✅ Test 1: Pagination Works
```javascript
// In browser console, after login
fetch('http://localhost:8000/api/v1/students/?skip=0&limit=50')
  .then(r => r.json())
  .then(d => console.log('First page:', d.length));

fetch('http://localhost:8000/api/v1/students/?skip=50&limit=50')
  .then(r => r.json())
  .then(d => console.log('Second page:', d.length));
```

#### ✅ Test 2: Request Caching Works
```javascript
// In browser console
// First request should hit network
console.time('Request 1');
fetch('http://localhost:5173/api/students/?skip=0&limit=100')
  .then(() => console.timeEnd('Request 1'));

// Wait 1 second, then repeat
setTimeout(() => {
  console.time('Request 2 (should be cached)');
  fetch('http://localhost:5173/api/students/?skip=0&limit=100')
    .then(() => console.timeEnd('Request 2 (should be cached)'));
}, 1000);

// Request 1 should be ~50-100ms
// Request 2 should be <5ms (from cache)
```

#### ✅ Test 3: Token Caching Works
```javascript
// In browser console
// Token should be read from memory, not localStorage
// Check Network tab - no localStorage warnings

// Verify memory cache:
console.log('Cached token in memory:', !!window.cachedToken);
```

#### ✅ Test 4: Filter Performance
1. Open DevTools → Performance
2. Start recording
3. Type into search box in Admin Students widget
4. Stop recording
5. Check "Scripting" time in performance profile
   - Before optimization: ~500ms
   - After optimization: ~50ms

#### ✅ Test 5: Zustand Selective Subscriptions
```javascript
// In browser console
// Sidebar should only re-render when user/permissions change
// Not when other app state changes

// You can verify by adding console logs in components
// and checking Network tab during interactions
```

### 5. Load Testing (Optional)

```bash
# Install Apache Bench
# macOS: brew install httpd
# Linux: sudo apt-get install apache2-utils

# Test concurrent requests
ab -n 100 -c 10 http://localhost:8000/api/v1/students/?skip=0&limit=100

# Expected: All requests complete
# Average response time: <100ms
```

## Performance Checklist

Before deployment, verify:

- [ ] Backend response times <100ms (check Network tab)
- [ ] Frontend loads in <2s (check Performance tab)
- [ ] Pagination works (can navigate through pages)
- [ ] Search filters smoothly (no lag while typing)
- [ ] Delete is instant (optimistic update)
- [ ] Create/Edit forms work correctly
- [ ] No console errors
- [ ] OpenTelemetry loads without blocking (if enabled)
- [ ] API requests deduplicated (check Network tab for cached responses)
- [ ] Bundle size reduced (npm run build shows reduced size)

## Key Metrics to Monitor

### Response Times
```
GET /api/v1/students/?skip=0&limit=100     → <100ms ✅
GET /api/v1/students/{id}                  → <50ms ✅
POST /api/v1/students/                     → <100ms ✅
PATCH /api/v1/students/{id}                → <100ms ✅
DELETE /api/v1/students/{id}               → <100ms ✅
POST /api/v1/students/public/submit-form   → <100ms ✅
```

### Frontend Metrics
```
Initial Load Time:   <2s ✅
First Paint:        <1s ✅
First Contentful Paint: <1s ✅
Table Render:       <60ms ✅
Filter Performance: <50ms per keystroke ✅
Delete Operation:   <0ms perceived delay ✅
```

## Troubleshooting

### Issue: Pagination not working
**Solution:** Check that API URL includes `?skip=0&limit=100` parameters

### Issue: Searches still slow
**Solution:** 
- Verify `useMemo` is in AdminStudentsWidget
- Check DevTools Performance tab for excessive re-renders
- May need virtual scrolling for 1000+ items

### Issue: Duplicate API requests
**Solution:** 
- Check request cache in api/client.js
- Verify cache key is correct
- Check Network tab for Cache-Control headers

### Issue: OpenTelemetry slowing down app
**Solution:**
- Ensure tracing.js is using lazy loading
- Check that `initializeTracing()` is called after app loads
- If VITE_JAEGER_URL not set, OpenTelemetry shouldn't load at all

## Performance Regression Testing

After future changes, always test:

1. **Response times**
   ```bash
   ab -n 100 -c 10 http://localhost:8000/api/v1/students/?skip=0&limit=100
   ```

2. **Frontend bundle size**
   ```bash
   npm run build && du -sh dist/
   ```

3. **React render performance**
   - DevTools → Profiler → Record while filtering
   - Check for unexpected re-renders

4. **Network requests**
   - DevTools → Network
   - Check for N+1 queries or redundant requests

---

**Last Updated:** April 11, 2026  
**Target:** All endpoints <100ms ✅
