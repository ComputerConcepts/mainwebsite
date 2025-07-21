# 🔧 MODAL TROUBLESHOOTING GUIDE

## Issue: Transfer Ownership Modal Not Working Properly

### 🎯 Quick Test Steps

1. **Load the page** with the file detail
2. **Open Developer Tools** (F12) → Console
3. **Run these commands** one by one:

```javascript
// Test 1: Check if modal elements exist
console.log('Modal:', document.getElementById('transferOwnershipModal'));
console.log('Trigger:', document.querySelector('[data-bs-target="#transferOwnershipModal"]'));

// Test 2: Check Bootstrap
console.log('Bootstrap:', typeof bootstrap);

// Test 3: Try to show modal programmatically
testModal();

// Test 4: If modal doesn't work, fix common issues
fixModalIssues();

// Test 5: Try clicking the button
document.querySelector('[data-bs-target="#transferOwnershipModal"]').click();
```

### 🔧 Common Modal Issues & Fixes

#### Issue 1: Modal Button Does Nothing
**Symptoms**: Clicking "Transfer" button does nothing
**Causes**: 
- Bootstrap not loaded properly
- Missing `data-bs-toggle="modal"` attribute
- Z-index conflicts

**Fix**:
```javascript
fixModalIssues();
```

#### Issue 2: Modal Opens But Form Doesn't Work
**Symptoms**: Modal opens but autocomplete/form doesn't work
**Causes**:
- Event listeners not attached
- API endpoints not working
- Form elements missing

**Test**:
```javascript
// Check form elements
console.log('Search input:', document.getElementById('newOwnerSearch'));
console.log('Hidden input:', document.getElementById('newOwner'));

// Test API
fetch('/api/employees/search-email/?q=admin')
  .then(r => r.json())
  .then(data => console.log('API Response:', data));
```

#### Issue 3: Modal Backdrop Stuck
**Symptoms**: Can't interact with page, dark overlay stuck
**Fix**:
```javascript
// Remove stuck backdrops
document.querySelectorAll('.modal-backdrop').forEach(b => b.remove());
document.body.classList.remove('modal-open');
document.body.style.paddingRight = '';
```

#### Issue 4: Modal Opens But Autocomplete Doesn't Work
**Symptoms**: Can open modal but typing in search field does nothing
**Check**:
```javascript
// Test if autocomplete function exists
console.log('handleOwnerSearch function:', typeof handleOwnerSearch);

// Test API endpoint directly
fetch('/api/employees/search-email/?q=test')
  .then(response => {
    console.log('API Status:', response.status);
    return response.json();
  })
  .then(data => console.log('API Data:', data))
  .catch(error => console.error('API Error:', error));
```

### 🏥 Emergency Modal Reset

If modal is completely broken, run this:

```javascript
// Nuclear option - reset everything
document.querySelectorAll('.modal-backdrop').forEach(b => b.remove());
document.body.classList.remove('modal-open');
document.body.style.overflow = '';
document.body.style.paddingRight = '';

const modal = document.getElementById('transferOwnershipModal');
if (modal) {
    modal.style.display = '';
    modal.setAttribute('aria-hidden', 'true');
    modal.classList.remove('show');
}

// Force reload if needed
// location.reload();
```

### 📋 What to Check in Console

1. **No JavaScript errors** when page loads
2. **Bootstrap is loaded**: `typeof bootstrap !== 'undefined'`
3. **Modal elements exist**: Both modal and trigger button found
4. **API works**: Employee search returns data
5. **Event listeners attached**: No errors when typing in search

### 🚀 Next Steps

1. Try the quick tests above
2. Report which step fails
3. If all tests pass but modal still doesn't work, we'll need to check:
   - Network tab for API calls
   - Server logs for backend issues
   - Bootstrap version compatibility

### 🔧 Files Modified for Debugging
- Added modal event listeners in `file_detail.html`
- Added CSS z-index fixes
- Added debugging functions: `testModal()`, `fixModalIssues()`
- Created modal diagnostic script: `debug_modal.js`
