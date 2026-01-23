# ✅ Unified Admin Guide - Single Login System

## 🎯 Overview

You now have **ONE unified admin system** where you:
- ✅ Login with your **main backend superuser** (not separate credentials)
- ✅ Manage **all companies** and their billing from one place
- ✅ View **billing status, invoices, payments** without switching admin panels
- ✅ **Both services communicate** automatically

## 🚀 Services Running

### Service Status

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Main Backend** | 8000 | http://localhost:8000/ | **LOGIN HERE** - Unified admin |
| **Billing Service** | 8002 | http://localhost:8002/ | Backend API (no login needed) |

### Check Services Are Running

```powershell
# Check billing service
curl.exe http://localhost:8002/api/billing/plans/
# Should return: {"success": true, "data": {"plans": []}}

# Check main backend  
curl.exe http://localhost:8000/admin/
# Should return HTML
```

## 📍 How to Use - Step by Step

### Step 1: Access the Unified Admin

1. **Open browser**: http://localhost:8000/admin/

2. **Login with YOUR existing superuser**:
   - Username: `<your_quidpath_backend_superuser>`
   - Password: `<your_password>`

3. **You're now in!** No separate login needed for billing.

### Step 2: View All Companies with Billing Status

1. Navigate to: **OrgAuth → Corporates**

2. You'll see a list with columns:
   ```
   ID | Name | Email | BILLING STATUS | Is Approved | Created
   ```

3. **Billing Status** shows:
   - ✅ **Active** (green) - Has paid subscription
   - 🆓 **Trial (X days)** (orange) - Using free trial
   - ❌ **Expired** (red) - No active subscription/trial

### Step 3: View Detailed Billing for a Company

1. **Click on any company** from the list

2. Scroll down to **"Billing Information"** section

3. **Click to expand** and see:
   ```
   📊 Billing Overview
   
   ✅ Trial Status
      Status: ACTIVE
      Days Remaining: 25 days
      End Date: February 5, 2026
   
   💼 Active Subscription (if subscribed)
      Plan: Professional Plan
      Billing Cycle: MONTHLY  
      Amount: KES 9,999.00
      End Date: March 5, 2026
   
   💰 Financial Summary
      Total Invoiced: KES 19,998.00
      Total Paid: KES 9,999.00
      Outstanding: KES 9,999.00
   
   📄 Recent Invoices
      [Table with invoice details]
   
   💳 Recent Payments
      [Table with payment history]
   ```

## 🔄 How the Services Communicate

### Architecture

```
┌─────────────────────────────────────────┐
│   YOU LOGIN HERE (Port 8000)            │
│   http://localhost:8000/admin/          │
│                                         │
│   Main Backend Admin                    │
│   - Uses YOUR superuser                 │
│   - Shows all companies                 │
│   - Displays billing data               │
└────────────┬────────────────────────────┘
             │
             │ When you view a company,
             │ main backend automatically calls:
             │
             ▼
┌─────────────────────────────────────────┐
│   Billing Service (Port 8002)           │
│   http://localhost:8002/                │
│                                         │
│   Backend API Only                      │
│   - NO login needed here                │
│   - Responds to API requests            │
│   - Returns billing data                │
└─────────────────────────────────────────┘
```

### Communication Flow

When you click on a company in the admin:

1. **Main Backend** extracts `corporate_id`
2. **Main Backend** calls: `GET http://localhost:8002/api/admin/billing/corporate/{corporate_id}/summary/`
3. **Billing Service** returns JSON with:
   - Trial status
   - Subscription details
   - Invoices list
   - Payments list
   - Financial totals
4. **Main Backend** formats data as beautiful HTML
5. **You see** complete billing information

### No Manual API Calls Needed!

Everything happens **automatically** when you:
- View the corporate list (shows billing status)
- Click on a company (loads detailed billing data)

## 📝 Common Tasks

### Task 1: Check Which Companies Are Paying

1. Go to: http://localhost:8000/admin/OrgAuth/corporate/
2. Look at **"Billing Status"** column
3. Green ✅ = Paying customers
4. Red ❌ = Need to subscribe

### Task 2: View Unpaid Invoices for a Company

1. Click on the company
2. Scroll to **"Billing Information"**  
3. Look at **"Outstanding"** amount
4. See list of pending invoices

### Task 3: Check Trial Expiration

1. View company details
2. In **"Billing Information"** section
3. See **"Trial Status"** with days remaining

### Task 4: Create Trial for New Company

**From main backend admin:**

```python
# Django shell
python manage.py shell

from quidpath_backend.core.billing_client import BillingServiceClient
client = BillingServiceClient()

# Create trial
result = client.create_trial(
    corporate_id='<company_uuid>',
    corporate_name='Company Name',
    plan_tier='starter'
)
```

**Or use API directly:**

```bash
curl -X POST http://localhost:8002/api/billing/trials/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "corporate_id": "uuid-here",
    "corporate_name": "Company Name",
    "plan_tier": "starter"
  }'
```

## 🔍 Verifying Communication

### Test 1: Check Services Are Talking

Open two terminals:

**Terminal 1 - Watch billing logs:**
```powershell
docker logs -f billing-backend-dev
```

**Terminal 2 - Access main admin:**
```powershell
# Open browser and view a company
# You should see API requests in Terminal 1
```

### Test 2: Check Billing Data Loads

1. Login to http://localhost:8000/admin/
2. Go to OrgAuth → Corporates
3. Click any company
4. If you see "Error loading billing data" → services aren't communicating
5. If you see billing details → ✅ Working!

### Test 3: Manual API Check

```powershell
# From main backend container
docker exec -it django-backend-dev curl http://host.docker.internal:8002/api/billing/plans/

# Should return JSON with plans
```

## 🐛 Troubleshooting

### Problem: "Error loading billing data"

**Cause**: Services can't communicate

**Fix**:
```powershell
# Check both services are running
docker ps

# Should see:
# - billing-backend-dev (port 8002)
# - django-backend-dev (port 8000)

# Restart if needed
cd e:\billing
docker compose -f docker-compose.dev.yml restart

cd e:\quidpath-backend  
docker compose -f docker-compose.dev.yml restart
```

### Problem: Billing status not showing

**Cause**: Billing service not responding

**Fix**:
```powershell
# Test billing service
curl.exe http://localhost:8002/api/billing/plans/

# If no response, restart:
cd e:\billing
docker compose -f docker-compose.dev.yml restart web
```

### Problem: Can't login to main admin

**Cause**: No superuser in main backend

**Fix**:
```powershell
# Create superuser in main backend
docker exec -it django-backend-dev python manage.py createsuperuser
```

## ⚙️ Configuration

### Main Backend Settings

File: `e:\quidpath-backend\quidpath_backend\settings\base.py`

```python
# Billing service URL
BILLING_SERVICE_URL = os.environ.get(
    "BILLING_SERVICE_URL",
    "http://localhost:8002/api/billing"  # ← Points to billing service
)
```

### Billing Service Settings

File: `e:\billing\docker-compose.dev.yml`

```yaml
environment:
  DATABASE_URL: postgresql://devuser:devpass@db:5432/billing_devdb
  # Billing runs on port 8002
```

## 🎯 Key Points

### ✅ DO:
- Login at http://localhost:8000/admin/
- Use your main backend superuser
- View billing in Corporate admin
- Let services communicate automatically

### ❌ DON'T:
- Try to login at http://localhost:8002/admin/
- Create separate superuser for billing
- Manually call billing APIs (unless developing)
- Stop billing service when using main admin

## 📊 What You Can See

### In Corporate List View

| Company | Email | **Billing Status** | Approved | Created |
|---------|-------|-------------------|----------|---------|
| Acme Corp | admin@acme.com | ✅ **Active** | Yes | Jan 1 |
| Test Co | test@test.com | 🆓 **Trial (15d)** | Yes | Jan 2 |
| Old Corp | old@old.com | ❌ **Expired** | Yes | Dec 1 |

### In Company Detail View

**Billing Information** (expandable section):
- 📊 Trial/Subscription status
- 💰 Financial summary (invoiced, paid, outstanding)
- 📄 Recent invoices with status
- 💳 Recent payments with method

## 🔐 Security

### Single Sign-On Flow

```
1. You → Login to main backend (port 8000)
2. Main backend → Checks your credentials
3. You authenticated → Can view all companies  
4. You view company → Main backend calls billing API
5. Billing API → Returns data (no separate auth needed)
6. Main backend → Shows you the data
```

**No separate authentication required for billing service!**

### Why This Is Secure

- **Main backend** handles all authentication
- **Billing service** only accepts API calls (no direct user login)
- **Data isolation**: Each company's data is separate
- **Corporate ID validation**: All billing requests verify company ownership

## 🎉 Benefits of This Setup

✅ **Single Login** - One username/password for everything  
✅ **Unified View** - All data in one admin panel  
✅ **Automatic Sync** - Services communicate in real-time  
✅ **Easy Management** - Track billing without switching tools  
✅ **Secure** - Proper data isolation and validation  
✅ **Scalable** - Microservice architecture  

## 📞 Quick Reference

| Task | URL | Credentials |
|------|-----|-------------|
| **Login to Admin** | http://localhost:8000/admin/ | Main backend superuser |
| **View Companies** | Admin → OrgAuth → Corporates | (same) |
| **View Billing** | Click company → Billing Information | (same) |
| **Test Billing API** | http://localhost:8002/api/billing/plans/ | No auth needed |

## 🚀 You're All Set!

**Both services are running and communicating properly:**
- ✅ Main Backend: Port 8000 (your admin login)
- ✅ Billing Service: Port 8002 (backend API)
- ✅ Integration: Working automatically
- ✅ Single Login: Use main backend superuser

**Login now**: http://localhost:8000/admin/

---

© 2026 Quidpath. All rights reserved.


