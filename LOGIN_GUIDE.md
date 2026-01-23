# 🔐 Login Guide - Billing & Main Backend

## ⚠️ IMPORTANT: Two Separate Systems

The billing microservice and main backend are **separate Django applications** with **separate user databases**. They communicate via API but do NOT share authentication.

---

## 🎯 RECOMMENDED APPROACH: Use Main Backend Admin Only

### ✅ How to Access Everything (Including Billing Data):

1. **Navigate to:** `http://localhost:8000/admin/`
2. **Login with:** Your quidpath-backend superuser credentials
3. **View Companies:** Click on "Corporates" in the admin panel
4. **See Billing Data:** 
   - In the list view, you'll see the "Billing Status" column
   - Click on any company to see detailed billing information
   - View trials, subscriptions, invoices, and payments

**This is the intended workflow!** You don't need to log in to the billing service directly.

---

## 🔧 ALTERNATIVE: Direct Billing Admin Access (Debugging Only)

### If you need to access the billing admin directly for debugging:

1. **Navigate to:** `http://localhost:8002/admin/`
2. **Login with:**
   - **Username:** `admin`
   - **Password:** `admin123`

### 🚨 If You Get CSRF Errors:

1. **Clear Browser Cache:**
   - Press `Ctrl + Shift + Delete`
   - Clear cookies and cached files
   - Try again

2. **Try Incognito/Private Window:**
   - Open a new incognito/private browsing window
   - Navigate to `http://localhost:8002/admin/`
   - Login with admin/admin123

3. **Check Container Logs:**
   ```powershell
   cd e:\billing
   docker compose -f docker-compose.dev.yml logs -f billing-backend-dev
   ```

---

## 📋 Quick Reference: Login Credentials

### Main Backend (Port 8000)
- **URL:** `http://localhost:8000/admin/`
- **Credentials:** Your quidpath-backend superuser
- **Database:** PostgreSQL (main backend DB)

### Billing Service (Port 8002)
- **URL:** `http://localhost:8002/admin/`
- **Credentials:** admin / admin123
- **Database:** PostgreSQL (billing DB - separate)

---

## 🔄 How Data Flows Between Services

```
┌─────────────────────────────────────────────────────────────────┐
│  Main Backend Admin (localhost:8000)                            │
│  - Login with quidpath-backend superuser                        │
│  - View Corporate list                                          │
│  - See billing status for each company                          │
│                                                                  │
│  When you click on a company:                                   │
│  ├── Fetches billing data via API call                          │
│  ├── BillingServiceClient.admin_get_corporate_summary()         │
│  └── Displays: Trials, Subscriptions, Invoices, Payments        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                         HTTP API Call
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Billing Service (localhost:8002)                               │
│  - Receives API request                                         │
│  - Returns billing data as JSON                                 │
│  - No authentication required for admin API endpoints           │
│    (protected by internal network)                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing the Integration

### Step 1: Verify Both Services Running
```powershell
# Check main backend
curl http://localhost:8000/admin/

# Check billing service
curl http://localhost:8002/admin/
```

### Step 2: Test Main Backend Admin
1. Go to `http://localhost:8000/admin/`
2. Login with your superuser
3. Navigate to Corporates
4. Click on any corporate
5. Scroll to "Billing Information" section
6. You should see trials, subscriptions, etc.

### Step 3: Test Billing API (Optional)
```powershell
# Test API endpoint
curl http://localhost:8002/api/admin/billing/stats/
```

---

## ❓ FAQ

**Q: Can I use my main backend credentials to login to billing service?**  
A: No. They are separate applications with separate databases.

**Q: Do I need to create a superuser for the billing service?**  
A: It's auto-created on startup (admin/admin123). But you don't need to use it for normal operations.

**Q: How do I see billing data for companies?**  
A: Login to main backend admin (localhost:8000) and view the Corporates section.

**Q: Why are there two separate admin panels?**  
A: Microservice architecture. The billing service is independent but integrated via API.

**Q: What if I forgot the billing admin password?**  
A: Default is admin/admin123. To reset, run:
```powershell
docker exec -it billing-backend-dev python manage.py changepassword admin
```

---

## 🐛 Troubleshooting

### CSRF Verification Failed
- Clear browser cookies
- Try incognito mode
- Restart billing service: `docker compose -f docker-compose.dev.yml restart`

### "Connection Refused" when accessing billing data
- Verify billing service is running: `docker ps`
- Check logs: `docker compose -f docker-compose.dev.yml logs`
- Verify BILLING_SERVICE_URL in main backend settings

### Billing data not showing in main admin
- Check that both services are running
- Verify the corporate has a UUID (not integer ID)
- Check main backend logs for API errors

---

## 📞 Need Help?

If you're still having issues:
1. Check container logs
2. Verify both services are running
3. Test API endpoints directly
4. Check network connectivity between containers

