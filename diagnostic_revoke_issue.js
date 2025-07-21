/*
DIAGNOSTIC SCRIPT FOR REVOKE ACCESS BUTTON ISSUES
Copy and paste this into the browser console on the production page
to diagnose the revoke access button problem.
*/

console.log('🔍 DIAGNOSING REVOKE ACCESS BUTTON ISSUES');
console.log('==========================================');

// 1. Check if the page has the necessary elements
const shareModal = document.getElementById('shareModal');
const shareItems = document.querySelectorAll('.share-item');
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');

console.log('📋 Element Check:');
console.log(`   Share Modal: ${shareModal ? '✅ Found' : '❌ Missing'}`);
console.log(`   Share Items: ${shareItems.length} found`);
console.log(`   CSRF Token: ${csrfToken ? '✅ Found' : '❌ Missing'}`);

if (csrfToken) {
    console.log(`   CSRF Value: ${csrfToken.value}`);
}

// 2. Check if revokeAccess function exists
console.log('\n📝 Function Check:');
console.log(`   revokeAccess function: ${typeof revokeAccess !== 'undefined' ? '✅ Found' : '❌ Missing'}`);

// 3. Get current file ID from URL
const currentUrl = window.location.pathname;
const fileIdMatch = currentUrl.match(/\/employee\/files\/view\/([^\/]+)\//);
const fileId = fileIdMatch ? fileIdMatch[1] : null;

console.log('\n🔗 URL Information:');
console.log(`   Current URL: ${currentUrl}`);
console.log(`   Extracted File ID: ${fileId || 'Not found'}`);

// 4. Check each share item for proper setup
console.log('\n👥 Share Items Analysis:');
shareItems.forEach((item, index) => {
    const shareId = item.getAttribute('data-share-id');
    const revokeButton = item.querySelector('button[onclick*="revokeAccess"]');
    
    console.log(`   Share ${index + 1}:`);
    console.log(`     Share ID: ${shareId || 'Missing'}`);
    console.log(`     Revoke Button: ${revokeButton ? '✅ Found' : '❌ Missing'}`);
    
    if (revokeButton) {
        const onclickAttr = revokeButton.getAttribute('onclick');
        console.log(`     onclick: ${onclickAttr}`);
    }
});

// 5. Test the unshare endpoint
if (fileId && shareItems.length > 0) {
    const firstShareId = shareItems[0].getAttribute('data-share-id');
    if (firstShareId) {
        const testUrl = `/employee/files/unshare/${fileId}/${firstShareId}/`;
        console.log('\n🧪 Testing Endpoint:');
        console.log(`   Test URL: ${testUrl}`);
        
        // Test with a HEAD request to see if endpoint exists
        fetch(testUrl, { 
            method: 'HEAD',
            headers: {
                'X-CSRFToken': csrfToken ? csrfToken.value : 'missing'
            }
        })
        .then(response => {
            console.log(`   Endpoint Response: ${response.status} ${response.statusText}`);
            if (response.status === 405) {
                console.log('   ✅ Endpoint exists (405 = Method Not Allowed for HEAD is expected)');
            } else if (response.status === 404) {
                console.log('   ❌ Endpoint not found (404)');
            } else {
                console.log(`   ℹ️ Unexpected response: ${response.status}`);
            }
        })
        .catch(error => {
            console.log(`   ❌ Network Error: ${error.message}`);
        });
    }
}

// 6. Provide a manual test function
window.testRevokeAccess = function(shareId, userName = 'Test User') {
    console.log('\n🔧 MANUAL REVOKE TEST:');
    console.log(`   Testing revoke for Share ID: ${shareId}`);
    
    if (!fileId) {
        console.log('   ❌ No file ID found in URL');
        return;
    }
    
    if (!csrfToken) {
        console.log('   ❌ No CSRF token found');
        return;
    }
    
    const url = `/employee/files/unshare/${fileId}/${shareId}/`;
    console.log(`   Request URL: ${url}`);
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken.value,
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log(`   Response Status: ${response.status} ${response.statusText}`);
        return response.json();
    })
    .then(data => {
        console.log('   Response Data:', data);
        if (data.success) {
            console.log('   ✅ Revoke successful!');
        } else {
            console.log('   ❌ Revoke failed:', data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.log('   ❌ Request failed:', error.message);
    });
};

console.log('\n💡 USAGE:');
console.log('   To manually test revoke access, run:');
if (shareItems.length > 0) {
    const firstShareId = shareItems[0].getAttribute('data-share-id');
    console.log(`   testRevokeAccess('${firstShareId}')`);
} else {
    console.log('   testRevokeAccess(\'SHARE_ID_HERE\')');
}

console.log('\n🔍 Check browser console for any JavaScript errors.');
console.log('🔍 Check Network tab in DevTools when clicking revoke button.');
