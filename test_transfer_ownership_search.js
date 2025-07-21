// TRANSFER OWNERSHIP SEARCHABLE FUNCTIONALITY TEST
// Run this in the browser console on file_detail.html to test the new searchable transfer ownership

console.log('🧪 TESTING SEARCHABLE TRANSFER OWNERSHIP FUNCTIONALITY');
console.log('====================================================');

// 1. Check if transfer ownership modal elements exist
const transferModal = document.getElementById('transferOwnershipModal');
const ownerSearchInput = document.getElementById('newOwnerSearch');
const hiddenOwnerInput = document.getElementById('newOwner');
const ownerSuggestions = document.getElementById('ownerSuggestions');
const selectedOwnerDiv = document.getElementById('selectedOwner');
const selectedOwnerName = document.getElementById('selectedOwnerName');

console.log(`📋 Transfer Ownership Elements Check:`);
console.log(`   Transfer Modal: ${transferModal ? '✅ Found' : '❌ Missing'}`);
console.log(`   Search Input: ${ownerSearchInput ? '✅ Found' : '❌ Missing'}`);
console.log(`   Hidden Input: ${hiddenOwnerInput ? '✅ Found' : '❌ Missing'}`);
console.log(`   Suggestions Container: ${ownerSuggestions ? '✅ Found' : '❌ Missing'}`);
console.log(`   Selected Owner Display: ${selectedOwnerDiv ? '✅ Found' : '❌ Missing'}`);

// 2. Check if functions exist
console.log(`\n🔧 Function Check:`);
console.log(`   selectOwner function: ${typeof window.selectOwner === 'function' ? '✅ Found' : '❌ Missing'}`);
console.log(`   clearOwnerSelection function: ${typeof window.clearOwnerSelection === 'function' ? '✅ Found' : '❌ Missing'}`);
console.log(`   transferOwnership function: ${typeof window.transferOwnership === 'function' ? '✅ Found' : '❌ Missing'}`);

// 3. Test the search functionality
window.testOwnerSearch = function(query = 'test') {
    console.log(`\n🔍 TESTING OWNER SEARCH with query: "${query}"`);
    
    if (!ownerSearchInput) {
        console.log('   ❌ Search input not found');
        return;
    }
    
    // Simulate typing
    ownerSearchInput.value = query;
    ownerSearchInput.dispatchEvent(new Event('input', { bubbles: true }));
    
    console.log('   📡 Search input event dispatched');
    console.log('   ⏳ Check the suggestions dropdown for results');
};

// 4. Test owner selection
window.testOwnerSelection = function(employeeId = '123', name = 'John Doe', email = 'john.doe@example.com') {
    console.log(`\n👤 TESTING OWNER SELECTION:`);
    console.log(`   Employee ID: ${employeeId}`);
    console.log(`   Name: ${name}`);
    console.log(`   Email: ${email}`);
    
    if (typeof window.selectOwner === 'function') {
        window.selectOwner(employeeId, name, email);
        console.log('   ✅ selectOwner function called');
        
        // Check if values were set correctly
        setTimeout(() => {
            const hiddenValue = hiddenOwnerInput ? hiddenOwnerInput.value : '';
            const displayText = selectedOwnerName ? selectedOwnerName.textContent : '';
            
            console.log(`   Hidden input value: "${hiddenValue}"`);
            console.log(`   Display text: "${displayText}"`);
            console.log(`   Search input hidden: ${ownerSearchInput ? (ownerSearchInput.style.display === 'none' ? '✅ Yes' : '❌ No') : 'N/A'}`);
            console.log(`   Selected owner shown: ${selectedOwnerDiv ? (selectedOwnerDiv.style.display === 'block' ? '✅ Yes' : '❌ No') : 'N/A'}`);
        }, 100);
    } else {
        console.log('   ❌ selectOwner function not available');
    }
};

// 5. Test clearing selection
window.testClearOwnerSelection = function() {
    console.log(`\n🔄 TESTING CLEAR OWNER SELECTION:`);
    
    if (typeof window.clearOwnerSelection === 'function') {
        window.clearOwnerSelection();
        console.log('   ✅ clearOwnerSelection function called');
        
        // Check if values were cleared correctly
        setTimeout(() => {
            const hiddenValue = hiddenOwnerInput ? hiddenOwnerInput.value : '';
            const searchValue = ownerSearchInput ? ownerSearchInput.value : '';
            
            console.log(`   Hidden input cleared: ${hiddenValue === '' ? '✅ Yes' : '❌ No'}`);
            console.log(`   Search input cleared: ${searchValue === '' ? '✅ Yes' : '❌ No'}`);
            console.log(`   Search input visible: ${ownerSearchInput ? (ownerSearchInput.style.display !== 'none' ? '✅ Yes' : '❌ No') : 'N/A'}`);
            console.log(`   Selected owner hidden: ${selectedOwnerDiv ? (selectedOwnerDiv.style.display === 'none' ? '✅ Yes' : '❌ No') : 'N/A'}`);
        }, 100);
    } else {
        console.log('   ❌ clearOwnerSelection function not available');
    }
};

// 6. Test the complete transfer workflow
window.testTransferWorkflow = function() {
    console.log(`\n🔄 TESTING COMPLETE TRANSFER WORKFLOW:`);
    
    // Step 1: Open modal
    if (transferModal) {
        console.log('   1. Opening transfer modal...');
        // You would manually open the modal in the UI
    }
    
    // Step 2: Search for an owner
    console.log('   2. Testing search functionality...');
    window.testOwnerSearch('john');
    
    // Step 3: Select an owner (after a delay to see search results)
    setTimeout(() => {
        console.log('   3. Testing owner selection...');
        window.testOwnerSelection('123', 'John Doe', 'john.doe@example.com');
        
        // Step 4: Test clearing selection
        setTimeout(() => {
            console.log('   4. Testing clear selection...');
            window.testClearOwnerSelection();
        }, 1000);
    }, 2000);
};

// 7. Check API endpoint
console.log(`\n🌐 API Endpoint Check:`);
console.log(`   Employee search endpoint: /api/employees/search-email/`);
console.log(`   This should be the same endpoint used for sharing autocomplete`);

// 8. Provide usage instructions
console.log(`\n💡 USAGE INSTRUCTIONS:`);
console.log(`   Basic Tests:`);
console.log(`   - testOwnerSearch('john') - Test searching for employees`);
console.log(`   - testOwnerSelection('123', 'John Doe', 'john@example.com') - Test selecting an owner`);
console.log(`   - testClearOwnerSelection() - Test clearing the selection`);
console.log(`   - testTransferWorkflow() - Test the complete workflow`);
console.log(`   `);
console.log(`   Manual Testing:`);
console.log(`   1. Click the "Transfer" button next to ownership`);
console.log(`   2. Start typing in the search field`);
console.log(`   3. Click on a suggestion to select`);
console.log(`   4. Verify the selected user appears`);
console.log(`   5. Click "Change" to clear selection`);
console.log(`   6. Fill in reason and check confirmation`);
console.log(`   7. Click "Transfer Ownership" to test the API call`);

console.log(`\n🔍 DEBUGGING TIPS:`);
console.log(`   - Check browser console for errors`);
console.log(`   - Check Network tab for API requests`);
console.log(`   - Verify CSRF token is present`);
console.log(`   - Ensure employee search API returns results`);
