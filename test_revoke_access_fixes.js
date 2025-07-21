// REVOKE ACCESS FUNCTIONALITY TEST
// Run this in the browser console on file_detail.html to test the revoke functionality

console.log('🧪 TESTING REVOKE ACCESS FUNCTIONALITY');
console.log('=====================================');

// 1. Check page elements
const shareModal = document.getElementById('shareModal');
const shareItems = document.querySelectorAll('[data-share-id]');
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');

console.log(`📋 Page Elements Check:`);
console.log(`   Share Modal: ${shareModal ? '✅ Found' : '❌ Missing'}`);
console.log(`   Share Items with data-share-id: ${shareItems.length}`);
console.log(`   CSRF Token: ${csrfToken ? '✅ Found' : '❌ Missing'}`);

// 2. Check if revokeAccess function exists and is properly defined
console.log(`\n🔧 Function Check:`);
console.log(`   revokeAccess function: ${typeof window.revokeAccess === 'function' ? '✅ Found' : '❌ Missing'}`);

// 3. Test URL structure
const currentUrl = window.location.pathname;
const fileIdMatch = currentUrl.match(/\/employee\/files\/view\/([^\/]+)\//);
const fileId = fileIdMatch ? fileIdMatch[1] : null;

console.log(`\n🔗 URL Analysis:`);
console.log(`   Current URL: ${currentUrl}`);
console.log(`   File ID: ${fileId || 'Not found'}`);

// 4. Analyze each share item
console.log(`\n👥 Share Items Analysis:`);
shareItems.forEach((item, index) => {
    const shareId = item.getAttribute('data-share-id');
    const revokeButton = item.querySelector('button[onclick*="revokeAccess"]');
    const userName = revokeButton ? revokeButton.getAttribute('onclick').match(/'([^']*)'[^']*$/)?.[1] : 'Unknown';
    
    console.log(`   Share ${index + 1}:`);
    console.log(`     Share ID: ${shareId}`);
    console.log(`     User Name: ${userName}`);
    console.log(`     Revoke Button: ${revokeButton ? '✅ Found' : '❌ Missing'}`);
    console.log(`     Location: ${item.closest('#shareModal') ? 'Modal' : 'Sidebar'}`);
});

// 5. Test function for manual verification
window.testRevokeAccessFixed = function(shareId, userName) {
    console.log(`\n🧪 MANUAL TEST: Revoking access for ${userName} (${shareId})`);
    
    if (typeof window.revokeAccess === 'function') {
        console.log('   Calling revokeAccess function...');
        window.revokeAccess(shareId, userName);
    } else {
        console.log('   ❌ revokeAccess function not available');
    }
};

// 6. Provide usage instructions
console.log(`\n💡 USAGE:`);
if (shareItems.length > 0) {
    const firstItem = shareItems[0];
    const firstShareId = firstItem.getAttribute('data-share-id');
    const firstButton = firstItem.querySelector('button[onclick*="revokeAccess"]');
    const firstUserName = firstButton ? firstButton.getAttribute('onclick').match(/'([^']*)'[^']*$/)?.[1] : 'Test User';
    
    console.log(`   To test revoke functionality, run:`);
    console.log(`   testRevokeAccessFixed('${firstShareId}', '${firstUserName}')`);
} else {
    console.log(`   No share items found to test with.`);
    console.log(`   Make sure the file is shared with someone first.`);
}

console.log(`\n🔍 DEBUGGING TIPS:`);
console.log(`   - Check browser console for errors when clicking revoke`);
console.log(`   - Check Network tab for HTTP requests and responses`);
console.log(`   - Verify CSRF token is being sent correctly`);
console.log(`   - Check that backend endpoint /employee/files/unshare/ exists`);
