// MODAL DIAGNOSTIC SCRIPT
// This script will help identify modal-related issues

console.log('🔧 MODAL DIAGNOSTIC SCRIPT LOADED');

// Test 1: Check if Bootstrap is loaded
function checkBootstrap() {
    console.log('\n1. 📦 CHECKING BOOTSTRAP:');
    
    if (typeof bootstrap !== 'undefined') {
        console.log('   ✅ Bootstrap JavaScript is loaded');
        console.log(`   📋 Bootstrap version: ${bootstrap.Tooltip.VERSION || 'Unknown'}`);
    } else {
        console.log('   ❌ Bootstrap JavaScript not found');
    }
    
    // Check for jQuery (older Bootstrap versions)
    if (typeof $ !== 'undefined') {
        console.log('   ✅ jQuery is loaded');
        console.log(`   📋 jQuery version: ${$.fn.jquery || 'Unknown'}`);
    } else {
        console.log('   ❌ jQuery not found');
    }
    
    // Check for modal CSS
    const modalElements = document.querySelectorAll('.modal');
    console.log(`   📋 Found ${modalElements.length} modal elements`);
}

// Test 2: Check modal elements
function checkModalElements() {
    console.log('\n2. 🎭 CHECKING MODAL ELEMENTS:');
    
    const modal = document.getElementById('transferOwnershipModal');
    const trigger = document.querySelector('[data-bs-target="#transferOwnershipModal"]');
    
    console.log(`   Modal element: ${modal ? '✅ Found' : '❌ Missing'}`);
    console.log(`   Trigger button: ${trigger ? '✅ Found' : '❌ Missing'}`);
    
    if (modal) {
        console.log(`   Modal classes: ${modal.className}`);
        console.log(`   Modal style: ${modal.style.display}`);
        console.log(`   Modal aria-hidden: ${modal.getAttribute('aria-hidden')}`);
    }
    
    if (trigger) {
        console.log(`   Trigger classes: ${trigger.className}`);
        console.log(`   Trigger data-bs-toggle: ${trigger.getAttribute('data-bs-toggle')}`);
        console.log(`   Trigger data-bs-target: ${trigger.getAttribute('data-bs-target')}`);
    }
    
    return { modal, trigger };
}

// Test 3: Check form elements inside modal
function checkModalForm() {
    console.log('\n3. 📋 CHECKING MODAL FORM ELEMENTS:');
    
    const elements = {
        newOwnerSearch: document.getElementById('newOwnerSearch'),
        newOwner: document.getElementById('newOwner'),
        transferReason: document.getElementById('transferReason'),
        confirmTransfer: document.getElementById('confirmTransfer'),
        ownerSuggestions: document.getElementById('ownerSuggestions'),
        selectedOwner: document.getElementById('selectedOwner'),
        selectedOwnerName: document.getElementById('selectedOwnerName')
    };
    
    Object.entries(elements).forEach(([name, element]) => {
        console.log(`   ${name}: ${element ? '✅ Found' : '❌ Missing'}`);
        if (element && element.value !== undefined) {
            console.log(`     Value: "${element.value}"`);
        }
    });
    
    return elements;
}

// Test 4: Test modal programmatically
function testModalProgrammatically() {
    console.log('\n4. 🧪 TESTING MODAL PROGRAMMATICALLY:');
    
    const modal = document.getElementById('transferOwnershipModal');
    if (!modal) {
        console.log('   ❌ Cannot test - modal not found');
        return false;
    }
    
    try {
        if (typeof bootstrap !== 'undefined') {
            console.log('   🔄 Testing with Bootstrap 5...');
            const modalInstance = bootstrap.Modal.getOrCreateInstance(modal);
            
            console.log('   📋 Modal instance created');
            console.log('   🔄 Attempting to show modal...');
            
            modalInstance.show();
            
            setTimeout(() => {
                console.log('   📋 Modal should be visible now');
                console.log(`   📋 Modal display: ${modal.style.display}`);
                console.log(`   📋 Modal aria-hidden: ${modal.getAttribute('aria-hidden')}`);
                
                console.log('   🔄 Hiding modal in 3 seconds...');
                setTimeout(() => {
                    modalInstance.hide();
                    console.log('   ✅ Modal test completed');
                }, 3000);
            }, 1000);
            
            return true;
        } else if (typeof $ !== 'undefined') {
            console.log('   🔄 Testing with Bootstrap 4/jQuery...');
            $(modal).modal('show');
            
            setTimeout(() => {
                console.log('   📋 Modal should be visible now');
                console.log('   🔄 Hiding modal in 3 seconds...');
                setTimeout(() => {
                    $(modal).modal('hide');
                    console.log('   ✅ Modal test completed');
                }, 3000);
            }, 1000);
            
            return true;
        } else {
            console.log('   ❌ No modal framework detected');
            return false;
        }
    } catch (error) {
        console.error('   ❌ Modal test failed:', error);
        return false;
    }
}

// Test 5: Check for conflicts
function checkForConflicts() {
    console.log('\n5. ⚠️ CHECKING FOR CONFLICTS:');
    
    // Check for multiple Bootstrap instances
    const bootstrapCSS = document.querySelectorAll('link[href*="bootstrap"]');
    const bootstrapJS = document.querySelectorAll('script[src*="bootstrap"]');
    
    console.log(`   Bootstrap CSS files: ${bootstrapCSS.length}`);
    console.log(`   Bootstrap JS files: ${bootstrapJS.length}`);
    
    if (bootstrapCSS.length > 1) {
        console.log('   ⚠️ Multiple Bootstrap CSS files detected - may cause conflicts');
    }
    
    if (bootstrapJS.length > 1) {
        console.log('   ⚠️ Multiple Bootstrap JS files detected - may cause conflicts');
    }
    
    // Check for backdrop issues
    const backdrops = document.querySelectorAll('.modal-backdrop');
    console.log(`   Modal backdrops: ${backdrops.length}`);
    
    // Check z-index issues
    const modal = document.getElementById('transferOwnershipModal');
    if (modal) {
        const computedStyle = window.getComputedStyle(modal);
        console.log(`   Modal z-index: ${computedStyle.zIndex}`);
        console.log(`   Modal position: ${computedStyle.position}`);
    }
}

// Test 6: Test button click
function testButtonClick() {
    console.log('\n6. 🖱️ TESTING BUTTON CLICK:');
    
    const trigger = document.querySelector('[data-bs-target="#transferOwnershipModal"]');
    if (!trigger) {
        console.log('   ❌ Trigger button not found');
        return false;
    }
    
    console.log('   ✅ Trigger button found');
    console.log('   🔄 Simulating click...');
    
    try {
        trigger.click();
        console.log('   ✅ Button click simulated');
        
        setTimeout(() => {
            const modal = document.getElementById('transferOwnershipModal');
            const isVisible = modal && (
                modal.style.display === 'block' ||
                modal.classList.contains('show') ||
                modal.getAttribute('aria-hidden') === 'false'
            );
            
            console.log(`   📋 Modal visible after click: ${isVisible ? '✅ Yes' : '❌ No'}`);
        }, 500);
        
        return true;
    } catch (error) {
        console.error('   ❌ Button click failed:', error);
        return false;
    }
}

// Main diagnostic function
function runModalDiagnostic() {
    console.log('🚀 RUNNING MODAL DIAGNOSTIC\n');
    
    checkBootstrap();
    const { modal, trigger } = checkModalElements();
    const formElements = checkModalForm();
    checkForConflicts();
    
    if (modal && trigger) {
        console.log('\n💡 MODAL TESTS AVAILABLE:');
        console.log('   testModalProgrammatically() - Test modal show/hide');
        console.log('   testButtonClick() - Test trigger button');
        console.log('   fixCommonIssues() - Apply common fixes');
        
        return { modal, trigger, formElements };
    } else {
        console.log('\n❌ CRITICAL ISSUES FOUND');
        console.log('   Modal or trigger button missing - cannot proceed with tests');
        return null;
    }
}

// Fix common modal issues
function fixCommonIssues() {
    console.log('\n🔧 APPLYING COMMON MODAL FIXES:');
    
    // Fix 1: Ensure proper Bootstrap attributes
    const trigger = document.querySelector('[data-bs-target="#transferOwnershipModal"]');
    if (trigger) {
        if (!trigger.getAttribute('data-bs-toggle')) {
            trigger.setAttribute('data-bs-toggle', 'modal');
            console.log('   ✅ Added missing data-bs-toggle="modal"');
        }
    }
    
    // Fix 2: Remove any stuck backdrops
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());
    if (backdrops.length > 0) {
        console.log(`   ✅ Removed ${backdrops.length} stuck backdrop(s)`);
    }
    
    // Fix 3: Reset modal state
    const modal = document.getElementById('transferOwnershipModal');
    if (modal) {
        modal.style.display = '';
        modal.setAttribute('aria-hidden', 'true');
        modal.classList.remove('show');
        console.log('   ✅ Reset modal state');
    }
    
    // Fix 4: Ensure body doesn't have modal-open class stuck
    if (document.body.classList.contains('modal-open')) {
        document.body.classList.remove('modal-open');
        console.log('   ✅ Removed modal-open class from body');
    }
    
    console.log('   🎯 Common fixes applied - try opening the modal now');
}

// Expose functions globally
window.runModalDiagnostic = runModalDiagnostic;
window.testModalProgrammatically = testModalProgrammatically;
window.testButtonClick = testButtonClick;
window.fixCommonIssues = fixCommonIssues;
window.checkBootstrap = checkBootstrap;

// Auto-run diagnostic
runModalDiagnostic();

console.log('\n💡 MODAL DIAGNOSTIC FUNCTIONS:');
console.log('   runModalDiagnostic() - Run full diagnostic again');
console.log('   testModalProgrammatically() - Test modal show/hide');
console.log('   testButtonClick() - Simulate button click');
console.log('   fixCommonIssues() - Fix common modal problems');
