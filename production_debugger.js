/* 
COMPREHENSIVE REVOKE ACCESS DEBUGGER
Copy this entire script into the browser console on the production page:
https://onecomputerconcepts.com/employee/files/view/480446df-19f5-4bbc-b63e-7387dd11c37f/
*/

console.log('🚀 PRODUCTION REVOKE ACCESS DEBUGGER v2.0');
console.log('=' + '='.repeat(50));

// Step 1: Environment Check
console.log('\n🔍 STEP 1: ENVIRONMENT CHECK');
console.log('-'.repeat(30));

const isProduction = window.location.hostname === 'onecomputerconcepts.com';
const currentUrl = window.location.href;
const fileIdMatch = currentUrl.match(/\/employee\/files\/view\/([^\/]+)\//);
const fileId = fileIdMatch ? fileIdMatch[1] : null;

console.log(`Environment: ${isProduction ? '🌐 Production' : '🏠 Local'}`);
console.log(`Current URL: ${currentUrl}`);
console.log(`File ID: ${fileId || '❌ Not found'}`);

// Step 2: Element Inspection
console.log('\n🔍 STEP 2: ELEMENT INSPECTION');
console.log('-'.repeat(30));

const shareModal = document.getElementById('shareModal');
const shareItems = document.querySelectorAll('.share-item');
const sidebarShares = document.querySelectorAll('button[onclick*="revokeAccess"]');
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');

console.log(`Share Modal: ${shareModal ? '✅ Found' : '❌ Missing'}`);
console.log(`Modal Share Items: ${shareItems.length} found`);
console.log(`Sidebar Revoke Buttons: ${sidebarShares.length} found`);
console.log(`CSRF Token: ${csrfToken ? '✅ Found' : '❌ Missing'}`);

if (csrfToken) {
    console.log(`CSRF Value: ${csrfToken.value.substring(0, 10)}...`);
}

// Step 3: Function Check
console.log('\n🔍 STEP 3: FUNCTION CHECK');
console.log('-'.repeat(30));

const hasRevokeFunction = typeof revokeAccess !== 'undefined';
console.log(`revokeAccess function: ${hasRevokeFunction ? '✅ Available' : '❌ Missing'}`);

if (hasRevokeFunction) {
    console.log('Function source preview:');
    console.log(revokeAccess.toString().substring(0, 200) + '...');
}

// Step 4: Share Items Analysis
console.log('\n🔍 STEP 4: SHARE ITEMS ANALYSIS');
console.log('-'.repeat(30));

const allShareData = [];

// Check modal share items
shareItems.forEach((item, index) => {
    const shareId = item.getAttribute('data-share-id');
    const userName = item.querySelector('h6')?.textContent?.trim();
    const revokeButton = item.querySelector('button[onclick*="revokeAccess"]');
    
    const shareData = {
        location: 'modal',
        index: index + 1,
        shareId: shareId,
        userName: userName,
        hasRevokeButton: !!revokeButton,
        onclickAttr: revokeButton?.getAttribute('onclick')
    };
    
    allShareData.push(shareData);
    
    console.log(`Modal Share ${index + 1}:`);
    console.log(`  Share ID: ${shareId || '❌ Missing'}`);
    console.log(`  User: ${userName || '❌ Missing'}`);
    console.log(`  Revoke Button: ${revokeButton ? '✅ Found' : '❌ Missing'}`);
    if (revokeButton) {
        console.log(`  onclick: ${revokeButton.getAttribute('onclick')}`);
    }
});

// Check sidebar share items
document.querySelectorAll('button[onclick*="revokeAccess"]').forEach((button, index) => {
    if (!button.closest('.share-item')) { // Only sidebar buttons
        const onclickAttr = button.getAttribute('onclick');
        const match = onclickAttr.match(/revokeAccess\('([^']+)',\s*'([^']+)'\)/);
        
        if (match) {
            const shareData = {
                location: 'sidebar',
                index: index + 1,
                shareId: match[1],
                userName: match[2],
                hasRevokeButton: true,
                onclickAttr: onclickAttr
            };
            
            allShareData.push(shareData);
            
            console.log(`Sidebar Share ${index + 1}:`);
            console.log(`  Share ID: ${match[1]}`);
            console.log(`  User: ${match[2]}`);
            console.log(`  onclick: ${onclickAttr}`);
        }
    }
});

// Step 5: Network Test
console.log('\n🔍 STEP 5: NETWORK CONNECTIVITY TEST');
console.log('-'.repeat(30));

if (fileId && allShareData.length > 0) {
    const testShareId = allShareData[0].shareId;
    const testUrl = `/employee/files/unshare/${fileId}/${testShareId}/`;
    
    console.log(`Testing endpoint: ${testUrl}`);
    
    fetch(testUrl, { 
        method: 'HEAD',
        headers: {
            'X-CSRFToken': csrfToken ? csrfToken.value : 'missing'
        }
    })
    .then(response => {
        console.log(`Endpoint test result: ${response.status} ${response.statusText}`);
        if (response.status === 405) {
            console.log('✅ Endpoint exists (405 Method Not Allowed is expected for HEAD request)');
        } else if (response.status === 404) {
            console.log('❌ Endpoint not found (404)');
        } else if (response.status === 403) {
            console.log('❌ Permission denied (403)');
        } else {
            console.log(`ℹ️ Unexpected status: ${response.status}`);
        }
    })
    .catch(error => {
        console.log(`❌ Network error: ${error.message}`);
    });
}

// Step 6: Enhanced Test Function
console.log('\n🔍 STEP 6: CREATING ENHANCED TEST FUNCTION');
console.log('-'.repeat(30));

window.testRevokeAccessEnhanced = function(shareId, userName) {
    console.log(`\n🧪 ENHANCED REVOKE TEST for ${userName}`);
    console.log('='.repeat(40));
    
    if (!fileId) {
        console.log('❌ No file ID found');
        return { success: false, error: 'No file ID' };
    }
    
    if (!csrfToken) {
        console.log('❌ No CSRF token found');
        return { success: false, error: 'No CSRF token' };
    }
    
    const url = `/employee/files/unshare/${fileId}/${shareId}/`;
    console.log(`Request URL: ${url}`);
    console.log(`CSRF Token: ${csrfToken.value.substring(0, 10)}...`);
    
    return fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken.value,
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
    .then(response => {
        console.log(`Response Status: ${response.status} ${response.statusText}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.json();
    })
    .then(data => {
        console.log('Response Data:', data);
        
        if (data.success) {
            console.log('✅ REVOKE SUCCESSFUL!');
            return { success: true, data: data };
        } else {
            console.log('❌ REVOKE FAILED:', data.error);
            return { success: false, error: data.error };
        }
    })
    .catch(error => {
        console.log('❌ REQUEST FAILED:', error.message);
        return { success: false, error: error.message };
    });
};

// Step 7: Auto-fix function
console.log('\n🔍 STEP 7: AUTO-FIX FUNCTION');
console.log('-'.repeat(30));

window.fixRevokeAccess = function() {
    console.log('🔧 APPLYING AUTO-FIX...');
    
    // Enhanced revokeAccess function
    window.revokeAccess = function(shareId, userName) {
        console.log(`🔧 Enhanced revoke for ${userName} (${shareId})`);
        
        if (!confirm(`Remove access for ${userName}?`)) {
            return;
        }
        
        if (!fileId || !csrfToken) {
            alert('Error: Missing file ID or security token. Please refresh the page.');
            return;
        }
        
        const url = `/employee/files/unshare/${fileId}/${shareId}/`;
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken.value,
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert(`Access removed for ${userName}`);
                location.reload(); // Simple reload for production
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Revoke error:', error);
            alert('Error removing access: ' + error.message);
        });
    };
    
    console.log('✅ Enhanced revokeAccess function installed');
    console.log('💡 Try clicking the revoke buttons now');
};

// Step 8: Usage Instructions
console.log('\n💡 USAGE INSTRUCTIONS');
console.log('='.repeat(50));
console.log('1. Review the analysis above for any red ❌ items');
console.log('2. To test revoke manually, run:');
if (allShareData.length > 0) {
    console.log(`   testRevokeAccessEnhanced('${allShareData[0].shareId}', '${allShareData[0].userName}')`);
}
console.log('3. To apply auto-fix, run:');
console.log('   fixRevokeAccess()');
console.log('4. Check Network tab in DevTools when clicking buttons');
console.log('5. Look for JavaScript errors in Console tab');

console.log('\n📊 SUMMARY');
console.log('='.repeat(50));
console.log(`File ID: ${fileId ? '✅' : '❌'}`);
console.log(`CSRF Token: ${csrfToken ? '✅' : '❌'}`);
console.log(`Share Items: ${allShareData.length} found`);
console.log(`Functions: ${hasRevokeFunction ? '✅' : '❌'}`);

if (allShareData.length === 0) {
    console.log('\n⚠️  No shares found to test. The file might not be shared with anyone.');
}
