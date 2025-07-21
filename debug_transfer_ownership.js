// TRANSFER OWNERSHIP DEBUGGING UTILITY
// Run this in the browser console to diagnose transfer ownership issues

console.log('🔧 TRANSFER OWNERSHIP DIAGNOSTIC TOOL');
console.log('=====================================');

function diagnoseTransferOwnership() {
    console.log('\n📋 CHECKING TRANSFER OWNERSHIP SETUP:');
    
    // 1. Check form elements
    const modal = document.getElementById('transferOwnershipModal');
    const searchInput = document.getElementById('newOwnerSearch');
    const hiddenInput = document.getElementById('newOwner');
    const reasonInput = document.getElementById('transferReason');
    const confirmCheckbox = document.getElementById('confirmTransfer');
    const selectedOwnerDiv = document.getElementById('selectedOwner');
    const selectedNameSpan = document.getElementById('selectedOwnerName');
    
    console.log('   Form Elements:');
    console.log(`     Modal: ${modal ? '✅ Found' : '❌ Missing'}`);
    console.log(`     Search Input: ${searchInput ? '✅ Found' : '❌ Missing'}`);
    console.log(`     Hidden Input: ${hiddenInput ? '✅ Found' : '❌ Missing'}`);
    console.log(`     Reason Input: ${reasonInput ? '✅ Found' : '❌ Missing'}`);
    console.log(`     Confirm Checkbox: ${confirmCheckbox ? '✅ Found' : '❌ Missing'}`);
    console.log(`     Selected Owner Display: ${selectedOwnerDiv ? '✅ Found' : '❌ Missing'}`);
    
    // 2. Check current values
    console.log('\n   Current Values:');
    console.log(`     Selected Employee ID: "${hiddenInput ? hiddenInput.value : 'N/A'}"`);
    console.log(`     Search Field Value: "${searchInput ? searchInput.value : 'N/A'}"`);
    console.log(`     Reason: "${reasonInput ? reasonInput.value : 'N/A'}"`);
    console.log(`     Confirmed: ${confirmCheckbox ? confirmCheckbox.checked : 'N/A'}`);
    console.log(`     Selected Name Display: "${selectedNameSpan ? selectedNameSpan.textContent : 'N/A'}"`);
    
    // 3. Check CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    console.log(`\n   Security:');
    console.log(`     CSRF Token: ${csrfToken ? '✅ Found' : '❌ Missing'}`);
    if (csrfToken) {
        console.log(`     CSRF Value: "${csrfToken.value}"`);
    }
    
    // 4. Check functions
    console.log('\n   Functions:');
    console.log(`     transferOwnership: ${typeof window.transferOwnership === 'function' ? '✅ Available' : '❌ Missing'}`);
    console.log(`     selectOwner: ${typeof window.selectOwner === 'function' ? '✅ Available' : '❌ Missing'}`);
    console.log(`     clearOwnerSelection: ${typeof window.clearOwnerSelection === 'function' ? '✅ Available' : '❌ Missing'}`);
    
    // 5. Get file ID from URL
    const currentUrl = window.location.pathname;
    const fileIdMatch = currentUrl.match(/\/employee\/files\/view\/([^\/]+)\//);
    const fileId = fileIdMatch ? fileIdMatch[1] : null;
    
    console.log('\n   File Information:');
    console.log(`     Current URL: ${currentUrl}`);
    console.log(`     File ID: ${fileId || 'Not found'}`);
    
    return {
        modal,
        searchInput,
        hiddenInput,
        reasonInput,
        confirmCheckbox,
        selectedOwnerDiv,
        selectedNameSpan,
        csrfToken,
        fileId
    };
}

// Function to test the API endpoint
function testTransferOwnershipAPI(employeeId, reason = 'Test transfer') {
    console.log('\n🧪 TESTING TRANSFER OWNERSHIP API:');
    
    const elements = diagnoseTransferOwnership();
    
    if (!elements.fileId) {
        console.log('   ❌ Cannot test - File ID not found in URL');
        return;
    }
    
    if (!elements.csrfToken) {
        console.log('   ❌ Cannot test - CSRF token not found');
        return;
    }
    
    if (!employeeId) {
        console.log('   ❌ Cannot test - Employee ID required');
        console.log('   Usage: testTransferOwnershipAPI("EMPLOYEE_ID_HERE", "Optional reason")');
        return;
    }
    
    const formData = new FormData();
    formData.append('new_owner_id', employeeId);
    formData.append('reason', reason);
    formData.append('csrfmiddlewaretoken', elements.csrfToken.value);
    
    const url = `/employee/files/transfer-ownership/${elements.fileId}/`;
    console.log(`   📡 Testing URL: ${url}`);
    console.log(`   📋 Employee ID: ${employeeId}`);
    console.log(`   📋 Reason: ${reason}`);
    
    fetch(url, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log(`   📡 Response: ${response.status} ${response.statusText}`);
        return response.json();
    })
    .then(data => {
        console.log('   📡 Response Data:', data);
        if (data.success) {
            console.log('   ✅ Transfer would succeed!');
            console.log('   ⚠️  Note: This was a real API call - the transfer may have actually happened!');
        } else {
            console.log('   ❌ Transfer failed:', data.error || data.message || 'Unknown error');
        }
    })
    .catch(error => {
        console.log('   ❌ API Error:', error);
    });
}

// Function to simulate the complete transfer process
function simulateTransferOwnership(employeeId, employeeName, employeeEmail, reason = 'Test transfer') {
    console.log('\n🎭 SIMULATING COMPLETE TRANSFER PROCESS:');
    
    const elements = diagnoseTransferOwnership();
    
    if (!elements.hiddenInput || !elements.confirmCheckbox) {
        console.log('   ❌ Cannot simulate - Required form elements missing');
        return;
    }
    
    console.log('   1. Selecting employee...');
    if (typeof window.selectOwner === 'function') {
        window.selectOwner(employeeId, employeeName, employeeEmail);
        console.log('   ✅ Employee selected');
    } else {
        // Manual selection
        elements.hiddenInput.value = employeeId;
        console.log('   ✅ Employee ID set manually');
    }
    
    console.log('   2. Setting reason...');
    if (elements.reasonInput) {
        elements.reasonInput.value = reason;
        console.log('   ✅ Reason set');
    }
    
    console.log('   3. Confirming transfer...');
    elements.confirmCheckbox.checked = true;
    console.log('   ✅ Transfer confirmed');
    
    console.log('   4. Ready to transfer!');
    console.log('   📋 Current form state:');
    console.log(`     Employee ID: "${elements.hiddenInput.value}"`);
    console.log(`     Reason: "${elements.reasonInput ? elements.reasonInput.value : 'N/A'}"`);
    console.log(`     Confirmed: ${elements.confirmCheckbox.checked}`);
    
    console.log('\n   💡 To complete the transfer, you can now:');
    console.log('      - Call transferOwnership() function');
    console.log('      - Or click the "Transfer Ownership" button');
    console.log('      - Or call testTransferOwnershipAPI() for API testing only');
    
    return elements;
}

// Main diagnostic function
window.diagnoseTransferOwnership = diagnoseTransferOwnership;
window.testTransferOwnershipAPI = testTransferOwnershipAPI;
window.simulateTransferOwnership = simulateTransferOwnership;

// Run initial diagnosis
diagnoseTransferOwnership();

console.log('\n💡 AVAILABLE FUNCTIONS:');
console.log('   diagnoseTransferOwnership() - Check current state');
console.log('   testTransferOwnershipAPI("EMPLOYEE_ID") - Test API directly');
console.log('   simulateTransferOwnership("123", "John Doe", "john@example.com") - Full simulation');
console.log('\n🔍 To debug the "Unknown error":');
console.log('   1. Run diagnoseTransferOwnership() to check setup');
console.log('   2. Open the transfer modal and select an employee');
console.log('   3. Run diagnoseTransferOwnership() again to see values');
console.log('   4. Check browser Network tab when clicking Transfer');
console.log('   5. Look for specific error messages in console');
