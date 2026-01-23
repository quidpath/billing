# 🚀 START HERE - Your Unified Admin System

## ⚡ Quick Start (30 seconds)

### 1️⃣ Open Your Browser

Navigate to: **http://localhost:8000/admin/**

```
🌐 http://localhost:8000/admin/
   ↑
   This is your ONLY login point
```

### 2️⃣ Login

Use your **existing main backend superuser**:

```
Username: [your quidpath-backend username]
Password: [your quidpath-backend password]
```

❌ **DON'T** create new user  
❌ **DON'T** login at port 8002  
✅ **USE** your existing credentials

### 3️⃣ View Companies with Billing

Click: **OrgAuth** → **Corporates**

You'll see:

```
┌──────────────────────────────────────────────────────────┐
│ ID  │ Name      │ Email        │ BILLING STATUS │ Created │
├──────────────────────────────────────────────────────────┤
│ 1   │ Acme Corp │ acme@co.com  │ ✅ Active      │ Jan 1   │
│ 2   │ Test Inc  │ test@te.com  │ 🆓 Trial (15d) │ Jan 2   │
│ 3   │ Old Corp  │ old@old.com  │ ❌ Expired     │ Dec 1   │
└──────────────────────────────────────────────────────────┘
```

### 4️⃣ View Detailed Billing

1. **Click** on any company
2. **Scroll** down to "Billing Information"
3. **Click** to expand
4. **See** complete billing details:
   - ✅ Trial status
   - 💼 Subscription details
   - 💰 Financial summary
   - 📄 Invoices
   - 💳 Payments

---

## ✅ Services Status

Both services are running:

| Service | Status | Port | Purpose |
|---------|--------|------|---------|
| Main Backend | ✅ Running | 8000 | **Your admin** |
| Billing Service | ✅ Running | 8002 | Backend API |

**They communicate automatically!**

---

## 🎯 Key Points

### ✅ DO:
- Login at **http://localhost:8000/admin/**
- Use your **main backend superuser**
- View billing in **Corporate admin**

### ❌ DON'T:
- Try to login at http://localhost:8002/admin/
- Create separate billing superuser
- Manually call APIs

---

## 🐛 Troubleshooting

### Can't see billing status?

```powershell
# Restart billing service
cd e:\billing
docker compose -f docker-compose.dev.yml restart web
```

### Can't login?

- ✅ Make sure you're at: http://localhost:8000/admin/
- ✅ Use main backend credentials
- ❌ Don't try: http://localhost:8002/admin/

### Error loading billing data?

```powershell
# Check billing service is running
docker ps | findstr billing

# Should see: billing-backend-dev

# If not, start it:
cd e:\billing
docker compose -f docker-compose.dev.yml up -d
```

---

## 📚 More Documentation

- **UNIFIED_ADMIN_GUIDE.md** - Complete user guide
- **FINAL_INTEGRATION_STATUS.md** - Technical details & architecture
- **FIXED_ADMIN_INTEGRATION.md** - Integration implementation

---

## 🎉 You're Ready!

**Login now:** http://localhost:8000/admin/

Everything is integrated and working!

---

© 2026 Quidpath


