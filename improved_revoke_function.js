// IMPROVED REVOKE ACCESS FUNCTION
// This version includes better error handling and debugging

function revokeAccessImproved(shareId, userName) {
    console.log(`🔧 Attempting to revoke access for ${userName} (Share ID: ${shareId})`);
    
    // Get current file ID from URL
    const currentUrl = window.location.pathname;
    const fileIdMatch = currentUrl.match(/\/employee\/files\/view\/([^\/]+)\//);
    const fileId = fileIdMatch ? fileIdMatch[1] : null;
    
    if (!fileId) {
        console.error('❌ Could not extract file ID from URL:', currentUrl);
        alert('Error: Could not determine file ID from current page URL');
        return;
    }
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken || !csrfToken.value) {
        console.error('❌ CSRF token not found');
        alert('Error: Security token not found. Please refresh the page and try again.');
        return;
    }
    
    if (!confirm(`Remove access for ${userName}?`)) {
        console.log('🚫 User cancelled revoke action');
        return;
    }
    
    const url = `/employee/files/unshare/${fileId}/${shareId}/`;
    console.log(`📡 Making request to: ${url}`);
    
    // Show loading state
    const shareItem = document.querySelector(`[data-share-id="${shareId}"]`);
    const revokeButton = shareItem ? shareItem.querySelector('button[onclick*="revokeAccess"]') : null;
    
    if (revokeButton) {
        revokeButton.disabled = true;
        revokeButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken.value,
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin' // Ensure cookies are sent
    })
    .then(response => {
        console.log(`📡 Response status: ${response.status} ${response.statusText}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.json();
    })
    .then(data => {
        console.log('📡 Response data:', data);
        
        if (data.success) {
            console.log(`✅ Successfully revoked access for ${userName}`);
            alert(`Access removed for ${userName}`);
            
            // Remove the share item from the UI
            if (shareItem) {
                shareItem.style.transition = 'opacity 0.3s ease';
                shareItem.style.opacity = '0';
                setTimeout(() => {
                    shareItem.remove();
                    
                    // Update the count in the header
                    const currentSharesDiv = document.getElementById('currentShares');
                    if (currentSharesDiv) {
                        const remainingShares = currentSharesDiv.querySelectorAll('.share-item').length;
                        const headerText = document.querySelector('.card-header h6');
                        if (headerText) {
                            headerText.innerHTML = `<i class="fas fa-users me-2"></i>Currently shared with (${remainingShares})`;
                        }
                        
                        // If no shares left, show empty state
                        if (remainingShares === 0) {
                            currentSharesDiv.innerHTML = `
                                <div class="text-center py-4 text-muted">
                                    <i class="fas fa-share-alt fa-3x mb-3"></i>
                                    <p class="mb-0">This file isn't shared with anyone yet.</p>
                                    <p>Use the form above to share it with team members.</p>
                                </div>
                            `;
                        }
                    }
                }, 300);
            }
        } else {
            console.error('❌ Server returned error:', data.error);
            alert('Error: ' + (data.error || 'Unknown error occurred'));
            
            // Restore button
            if (revokeButton) {
                revokeButton.disabled = false;
                revokeButton.innerHTML = '<i class="fas fa-times"></i>';
            }
        }
    })
    .catch(error => {
        console.error('❌ Request failed:', error);
        alert('Error removing access: ' + error.message);
        
        // Restore button
        if (revokeButton) {
            revokeButton.disabled = false;
            revokeButton.innerHTML = '<i class="fas fa-times"></i>';
        }
    });
}

// Replace the existing revokeAccess function
window.revokeAccess = revokeAccessImproved;

console.log('✅ Improved revokeAccess function loaded');
console.log('💡 The revoke buttons should now work with better error handling');
