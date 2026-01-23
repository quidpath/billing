# Admin Integration Guide

## Overview

The billing microservice is now **fully integrated** into the main Quidpath backend admin panel. You can use the **same superuser credentials** to manage all billing data without needing to log into the billing service separately.

## ✅ What's Integrated

### 1. **Corporate Admin - Enhanced with Billing Info**

When you view a company in the admin panel (`/admin/OrgAuth/corporate/`), you'll now see:

- **Billing Status Column** in the list view:
  - 🆓 Trial (X days) - Orange
  - ✅ Active - Green  
  - ❌ Expired - Red

- **Billing Details Section** on the detail page:
  - Trial status and days remaining
  - Active subscription information
  - Financial summary (invoiced, paid, outstanding)
  - Recent invoices table
  - Recent payments table

### 2. **Billing Management Section** (Coming Soon)

A dedicated "Billing Management" section in the admin sidebar with links to:
- Billing Overview (statistics dashboard)
- All Trials
- All Subscriptions
- All Invoices
- All Payments

## 🚀 How to Use

### Step 1: Start Both Services

**Billing Service:**
```bash
cd e:\billing
docker compose -f docker-compose.dev.yml up
```

**Main Backend:**
```bash
cd e:\quidpath-backend
python manage.py runserver 8000
```

### Step 2: Log into Main Backend Admin

```
URL: http://localhost:8000/admin/
Username: <your_main_backend_superuser>
Password: <your_password>
```

**No need to log into the billing service separately!**

### Step 3: View Billing Information

#### Option A: View Specific Company Billing
1. Navigate to **OrgAuth → Corporates**
2. You'll see billing status for each company in the list
3. Click on any company
4. Scroll to the **"Billing Information"** section
5. Click to expand and see:
   - Trial/Subscription status
   - Financial summary
   - Recent invoices
   - Recent payments

#### Option B: View All Billing Data (If Custom Views Enabled)
1. Look for **"Billing Management"** in the admin sidebar
2. Click to see:
   - Overview dashboard with statistics
   - Lists of all trials
   - Lists of all subscriptions
   - Lists of all invoices
   - Lists of all payments

## 📊 What You Can See

### On Corporate Detail Page

**Billing Overview Section:**
```
📊 Billing Overview

✅ Trial Status
Status: ACTIVE
Days Remaining: 25
End Date: 2026-02-05

💼 Active Subscription
Plan: Professional Plan (professional)
Billing Cycle: MONTHLY
Amount: KES 9,999.00
End Date: 2026-03-05

💰 Financial Summary
Total Invoiced: KES 19,998.00
Total Paid: KES 9,999.00
Outstanding: KES 9,999.00

📄 Recent Invoices
[Table with invoice details]

💳 Recent Payments
[Table with payment history]
```

### In List View

Each company row shows:
- Company name
- Email
- **Billing Status**: 
  - 🆓 Trial (15 days)
  - ✅ Active
  - ❌ Expired
- Is Approved
- Created date

## 🔧 How It Works

### Architecture

```
Main Backend Admin Panel
         ↓
Corporate Admin (Enhanced)
         ↓
Fetches data using BillingServiceClient
         ↓
HTTP GET to Billing Service Admin API
         ↓
Returns billing data as JSON
         ↓
Displayed in beautiful HTML format
```

### Admin API Endpoints (Internal)

The billing service exposes these admin-only endpoints:

```
GET /api/admin/billing/trials/
GET /api/admin/billing/subscriptions/
GET /api/admin/billing/invoices/
GET /api/admin/billing/payments/
GET /api/admin/billing/stats/
GET /api/admin/billing/corporate/<corporate_id>/summary/
```

These are called automatically by the main backend admin when you view corporate pages.

## 🛡️ Security

### Access Control

- **Only superusers** can see billing information
- Admin endpoints are **internal-only** (not exposed to regular users)
- Uses HTTP communication between services (should be HTTPS in production)
- No separate authentication needed - uses main backend permissions

### Production Considerations

1. **Use HTTPS** for inter-service communication
2. **Add API authentication** between services (shared secret or JWT)
3. **Rate limiting** on admin API endpoints
4. **VPC/Network isolation** for billing service
5. **Audit logging** for admin actions

## 📝 Customization

### Adding More Fields to Corporate Admin

Edit `e:\quidpath-backend\OrgAuth\admin.py`:

```python
def get_billing_summary(self, obj):
    # Customize the HTML output here
    # Add more sections, different formatting, etc.
    pass
```

### Creating Custom Billing Admin Views

Edit `e:\quidpath-backend\quidpath_backend\core\admin.py`:

```python
class BillingOverviewAdmin(admin.ModelAdmin):
    def custom_view(self, request):
        # Add your custom view logic
        pass
```

## 🐛 Troubleshooting

### Billing Info Not Showing

**Problem**: Billing section is empty or shows error

**Solutions**:
1. Check billing service is running:
   ```bash
   curl http://localhost:8002/api/billing/plans/
   ```

2. Check admin API endpoint:
   ```bash
   curl http://localhost:8002/api/admin/billing/stats/
   ```

3. Check main backend logs for errors

4. Verify `BILLING_SERVICE_URL` in settings:
   ```python
   # settings/base.py
   BILLING_SERVICE_URL = os.environ.get(
       "BILLING_SERVICE_URL",
       "http://localhost:8002/api/billing"
   )
   ```

### Slow Page Load

**Problem**: Corporate detail page loads slowly

**Solution**: The admin makes API calls to fetch billing data. This can be slow if:
- Billing service is slow to respond
- Network latency between services
- Large amount of invoice/payment data

**Optimizations**:
1. Add caching (Redis) for billing data
2. Reduce number of records fetched (limit parameter)
3. Use async loading (AJAX) instead of sync
4. Add pagination to invoice/payment tables

### Permission Denied

**Problem**: Can't see billing information

**Solution**:
1. Make sure you're logged in as superuser
2. Check `request.user.is_superuser` returns True
3. Verify user has permission to view Corporate model

## 🎨 Visual Examples

### Corporate List View
```
NAME          EMAIL               BILLING STATUS    IS APPROVED  CREATED
────────────────────────────────────────────────────────────────────────
Acme Corp     admin@acme.com      ✅ Active         Yes          Jan 1, 2026
Test Co       test@test.com       🆓 Trial (15d)    Yes          Jan 2, 2026
Old Corp      old@corp.com        ❌ Expired        Yes          Dec 1, 2025
```

### Corporate Detail View
```
COMPANY INFORMATION
  Name: Acme Corp
  Industry: Technology
  ...

BILLING INFORMATION  [Click to expand]
  ┌─────────────────────────────────────────┐
  │ 📊 Billing Overview                     │
  │                                         │
  │ ✅ Trial Status: ACTIVE (15 days)       │
  │ 💰 Total Paid: KES 9,999.00            │
  │ ⚠️ Outstanding: KES 0.00               │
  │                                         │
  │ [Recent Invoices Table]                 │
  │ [Recent Payments Table]                 │
  └─────────────────────────────────────────┘
```

## 📚 Related Documentation

- **[BILLING_INTEGRATION_GUIDE.md](BILLING_INTEGRATION_GUIDE.md)** - Full API documentation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[QUICK_START.md](QUICK_START.md)** - Quick setup guide

## 🎯 Benefits

✅ **Single Login** - Use main backend superuser for everything
✅ **Centralized Management** - All data in one admin panel
✅ **Complete Visibility** - See billing status for every company
✅ **Easy Tracking** - Monitor trials, subscriptions, invoices, payments
✅ **No Context Switching** - No need to switch between admin panels

## 🚦 Testing

### Test the Integration

1. **Create a Test Company:**
   ```python
   # Django shell in main backend
   from OrgAuth.models import Corporate
   corp = Corporate.objects.create(
       name="Test Company",
       email="test@test.com",
       ...
   )
   ```

2. **Create Trial via Billing API:**
   ```bash
   curl -X POST http://localhost:8002/api/billing/trials/create/ \
     -H "Content-Type: application/json" \
     -d '{"corporate_id": "<corp_id>", "corporate_name": "Test Company", "plan_tier": "starter"}'
   ```

3. **View in Admin:**
   - Go to http://localhost:8000/admin/OrgAuth/corporate/
   - Find "Test Company"
   - Should see 🆓 Trial (30 days) in Billing Status column
   - Click on company
   - Scroll to Billing Information
   - Should see trial details

4. **Verify Data:**
   - Trial status should be "ACTIVE"
   - Days remaining should be 30
   - No subscriptions yet
   - No invoices yet

## 💡 Future Enhancements

- [ ] Add inline actions (e.g., "Send Invoice Reminder")
- [ ] Add filtering by billing status in list view
- [ ] Add bulk actions for billing operations
- [ ] Create charts and graphs in overview dashboard
- [ ] Add email notification triggers from admin
- [ ] Add invoice PDF download links
- [ ] Add payment retry functionality
- [ ] Create admin change logs for billing events

## 📞 Support

For issues with admin integration:
1. Check both services are running
2. Verify API endpoints are accessible
3. Check browser console for JavaScript errors
4. Review server logs for Python errors
5. Consult [BILLING_INTEGRATION_GUIDE.md](BILLING_INTEGRATION_GUIDE.md)

---

**Success!** You can now manage all billing from the main Quidpath admin panel using your existing superuser account. No separate login needed! 🎉

© 2026 Quidpath. All rights reserved.


