// COMPREHENSIVE TRANSFER OWNERSHIP DEBUGGING
// This script will help identify why transfer ownership "doesn't work"

console.log('🔧 COMPREHENSIVE TRANSFER OWNERSHIP DEBUG');
console.log('==========================================');

// Step 1: Check current file ownership
function checkCurrentOwnership() {
    console.log('\n1. 📋 CHECKING CURRENT FILE OWNERSHIP:');
    
    // Extract file ID from URL
    const currentUrl = window.location.pathname;
    const fileIdMatch = currentUrl.match(/\/employee\/files\/view\/([^\/]+)\//);
    const fileId = fileIdMatch ? fileIdMatch[1] : null;
    
    console.log(`   File ID: ${fileId}`);
    
    // Check who is displayed as the current owner
    const ownerElement = document.querySelector('.file-info-card strong');
    const currentOwner = ownerElement ? ownerElement.textContent : 'Unknown';
    console.log(`   Current owner (from UI): ${currentOwner}`);
    
    return { fileId, currentOwner };
}

// Step 2: Test the employee search API
function testEmployeeSearchAPI() {
    console.log('\n2. 🔍 TESTING EMPLOYEE SEARCH API:');
    
    return fetch('/api/employees/search-email/?q=test')
        .then(response => response.json())
        .then(data => {
            console.log(`   API Response:`, data);
            if (data.results && data.results.length > 0) {
                const employee = data.results[0];
                console.log(`   Sample employee:`, employee);
                console.log(`   Employee ID type: ${typeof employee.id}`);
                console.log(`   Employee ID value: "${employee.id}"`);
                return employee;
            } else {
                console.log('   ❌ No employees found');
                return null;
            }
        })
        .catch(error => {
            console.log(`   ❌ API Error:`, error);
            return null;
        });
}

// Step 3: Test form element setup
function testFormElements() {
    console.log('\n3. 📋 TESTING FORM ELEMENTS:');
    
    const elements = {
        transferModal: document.getElementById('transferOwnershipModal'),
        searchInput: document.getElementById('newOwnerSearch'),
        hiddenInput: document.getElementById('newOwner'),
        reasonInput: document.getElementById('transferReason'),
        confirmCheckbox: document.getElementById('confirmTransfer'),
        selectedDiv: document.getElementById('selectedOwner'),
        selectedNameSpan: document.getElementById('selectedOwnerName'),
        csrfToken: document.querySelector('[name=csrfmiddlewaretoken]')
    };
    
    Object.entries(elements).forEach(([name, element]) => {
        console.log(`   ${name}: ${element ? '✅ Found' : '❌ Missing'}`);
        if (element && element.value !== undefined) {
            console.log(`     Value: "${element.value}"`);
        }
    });
    
    return elements;
}

// Step 4: Simulate complete transfer process
function simulateCompleteTransfer() {
    console.log('\n4. 🎭 SIMULATING COMPLETE TRANSFER PROCESS:');
    
    return testEmployeeSearchAPI().then(employee => {
        if (!employee) {
            console.log('   ❌ Cannot simulate - no employee data available');
            return false;
        }
        
        const elements = testFormElements();
        if (!elements.hiddenInput || !elements.confirmCheckbox) {
            console.log('   ❌ Cannot simulate - missing form elements');
            return false;
        }
        
        console.log('   📝 Setting up form for simulation...');
        
        // Set employee selection
        if (typeof window.selectOwner === 'function') {
            console.log('   👤 Selecting employee via selectOwner function...');
            window.selectOwner(employee.id, employee.name, employee.email);
        } else {
            console.log('   👤 Setting employee manually...');
            elements.hiddenInput.value = employee.id;
        }
        
        // Set reason
        elements.reasonInput.value = 'Test transfer for debugging';
        
        // Set confirmation
        elements.confirmCheckbox.checked = true;
        
        console.log('   ✅ Form setup complete');
        console.log('   📋 Current form state:');
        console.log(`     Employee ID: "${elements.hiddenInput.value}"`);
        console.log(`     Reason: "${elements.reasonInput.value}"`);
        console.log(`     Confirmed: ${elements.confirmCheckbox.checked}`);
        
        return true;
    });
}

// Step 5: Test actual transfer API call
function testTransferAPI(employeeId, reason = 'Debug test') {
    console.log('\n5. 🧪 TESTING TRANSFER API CALL:');
    
    const { fileId } = checkCurrentOwnership();
    if (!fileId) {
        console.log('   ❌ Cannot test - no file ID found');
        return Promise.resolve(false);
    }
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        console.log('   ❌ Cannot test - no CSRF token found');
        return Promise.resolve(false);
    }
    
    console.log(`   📡 Testing transfer to employee ID: ${employeeId}`);
    console.log(`   📋 Reason: ${reason}`);
    
    const formData = new FormData();
    formData.append('new_owner_id', employeeId);
    formData.append('reason', reason);
    formData.append('csrfmiddlewaretoken', csrfToken.value);
    
    console.log('   📡 Form data:');
    for (let pair of formData.entries()) {
        console.log(`     ${pair[0]}: "${pair[1]}"`);
    }
    
    const transferUrl = `/employee/files/transfer-ownership/${fileId}/`;
    console.log(`   📡 Transfer URL: ${transferUrl}`);
    
    return fetch(transferUrl, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log(`   📡 Response status: ${response.status} ${response.statusText}`);
        console.log(`   📡 Response headers:`, Object.fromEntries(response.headers.entries()));
        
        if (!response.ok) {
            console.log(`   ❌ HTTP Error: ${response.status}`);
        }
        
        return response.json();
    })
    .then(data => {
        console.log('   📡 Response data:', data);
        console.log('   📡 Response type:', typeof data);
        console.log('   📡 Response keys:', Object.keys(data));
        
        if (data.success) {
            console.log('   ✅ Transfer API reports success');
            console.log('   💡 If ownership didn\'t change, check server logs');
        } else {
            console.log('   ❌ Transfer API reports failure');
            console.log(`   ❌ Error: ${data.error || data.message || 'Unknown'}`);
        }
        
        return data;
    })
    .catch(error => {
        console.log('   ❌ API call failed:', error);
        return { error: error.message };
    });
}

// Main debugging function
async function runCompleteDebug() {
    console.log('🚀 RUNNING COMPLETE TRANSFER OWNERSHIP DEBUG\n');
    
    // Step 1: Check current state
    const ownership = checkCurrentOwnership();
    
    // Step 2: Test API
    const employee = await testEmployeeSearchAPI();
    
    // Step 3: Test form elements
    const elements = testFormElements();
    
    // Step 4: Simulate setup
    const setupSuccess = await simulateCompleteTransfer();
    
    if (setupSuccess && employee) {
        console.log('\n💡 READY FOR TESTING');
        console.log('   You can now:');
        console.log(`   1. Call testTransferAPI('${employee.id}') to test the API directly`);
        console.log('   2. Click the "Transfer Ownership" button to test the UI');
        console.log('   3. Check browser Network tab for the actual request');
        console.log('   4. Check server logs for backend debugging output');
        
        // Ask if user wants to run the actual API test
        console.log('\n❓ To run the actual transfer API test, type:');
        console.log(`   testTransferAPI('${employee.id}')`);
        
        return { ownership, employee, elements, setupSuccess };
    } else {
        console.log('\n❌ DEBUG SETUP FAILED');
        console.log('   Check the issues above before proceeding');
        return null;
    }
}

// Expose functions globally
window.checkCurrentOwnership = checkCurrentOwnership;
window.testEmployeeSearchAPI = testEmployeeSearchAPI;
window.testFormElements = testFormElements;
window.simulateCompleteTransfer = simulateCompleteTransfer;
window.testTransferAPI = testTransferAPI;
window.runCompleteDebug = runCompleteDebug;

// Check if we're on a file detail page
if (window.location.pathname.includes('/employee/files/view/')) {
    // Auto-run the complete debug
    runCompleteDebug().then(result => {
        if (result) {
            console.log('\n🎯 DEBUG COMPLETED SUCCESSFULLY');
            console.log('   Use the available functions to dig deeper into specific issues');
        }
    });
} else {
    console.log('💡 DEBUG SCRIPT LOADED');
    console.log('   Navigate to a file detail page to run automatic debugging');
    console.log('   Or call runCompleteDebug() manually');
}

console.log('\n💡 AVAILABLE DEBUG FUNCTIONS:');
console.log('   runCompleteDebug() - Run all tests again');
console.log('   checkCurrentOwnership() - Check file ownership info');
console.log('   testEmployeeSearchAPI() - Test the search API');
console.log('   testFormElements() - Check form element status');
console.log('   simulateCompleteTransfer() - Set up form for testing');
console.log('   testTransferAPI(employeeId) - Test the transfer API directly');
