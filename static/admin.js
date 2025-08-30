/**
 * Admin JavaScript functionality for Stabsspel
 * Extracted from inline scripts for better organization
 */

// Timer functionality
function openTimerWindow(spelId) {
    // Hämta aktuell tid och status från admin-timern
    var timerElement = document.getElementById('timer');
    var statusElement = document.querySelector('.status');
    
    var currentTime = timerElement ? timerElement.textContent : '10:00';
    var currentStatus = statusElement ? statusElement.textContent.toLowerCase().replace('status: ', '') : 'paused';
    
    // Konvertera tid till sekunder (t.ex. "09:21" -> 561)
    var timeParts = currentTime.split(':');
    var minutes = parseInt(timeParts[0]);
    var seconds = parseInt(timeParts[1]);
    var totalSeconds = minutes * 60 + seconds;
    
    var timerWindow = window.open(`/timer_window/${spelId}?time=${totalSeconds}&status=${currentStatus}`, 'timerWindow', 'width=800,height=600,scrollbars=no,resizable=yes');
    if (timerWindow) {
        timerWindow.focus();
    }
}

// Checkbox state management
function saveCheckboxState(checkboxId, checked) {
    fetch('/admin/save_checkbox', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            checkbox_id: checkboxId,
            checked: checked
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Checkbox state saved successfully');
        } else {
            console.error('Failed to save checkbox state');
        }
    })
    .catch(error => {
        console.error('Error saving checkbox state:', error);
    });
}

// Button state management
function updateNextFasButton() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    const nextFasButton = document.getElementById('next_fas_button');
    
    if (nextFasButton) {
        nextFasButton.disabled = !allChecked;
        nextFasButton.style.opacity = allChecked ? '1' : '0.5';
    }
}

function updateDiploNextFasButton() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    const nextFasButton = document.getElementById('diplo_next_fas_button');
    
    if (nextFasButton) {
        nextFasButton.disabled = !allChecked;
        nextFasButton.style.opacity = allChecked ? '1' : '0.5';
    }
}

function updateStartButton() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    const startButton = document.getElementById('start_button');
    
    if (startButton) {
        startButton.disabled = !allChecked;
        startButton.style.opacity = allChecked ? '1' : '0.5';
    }
}

// Test mode functionality
function toggleTestMode() {
    const testModeToggle = document.getElementById('test_mode_toggle');
    const cheatLinks = document.querySelectorAll('.cheat-link');
    
    if (testModeToggle && cheatLinks.length > 0) {
        const isVisible = testModeToggle.checked;
        cheatLinks.forEach(link => {
            link.style.display = isVisible ? 'inline-block' : 'none';
        });
    }
}

// Auto-fill functionality
function autoFillOrders() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
    });
    updateNextFasButton();
}

// Refresh functionality
function refreshChecklist() {
    location.reload();
}

// Timer maximization
function toggleTimerMaximize() {
    var timerContainer = document.querySelector('.timer-container');
    var maximizeBtn = document.querySelector('.maximize-btn');
    var minimizeBtn = document.querySelector('.minimize-btn');
    var body = document.body;
    
    if (timerContainer.classList.contains('maximized')) {
        // Minimize timer
        timerContainer.classList.remove('maximized');
        body.classList.remove('timer-maximized');
        maximizeBtn.style.display = 'inline-block';
        minimizeBtn.style.display = 'none';
    } else {
        // Maximize timer
        timerContainer.classList.add('maximized');
        body.classList.add('timer-maximized');
        maximizeBtn.style.display = 'none';
        minimizeBtn.style.display = 'inline-block';
    }
}

// Copy to clipboard functionality
function copyToClipboard() {
    const textToCopy = document.getElementById('text-to-copy').textContent;
    
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(textToCopy).then(function() {
            showCopySuccess();
        }).catch(function(err) {
            console.error('Could not copy text: ', err);
            fallbackCopyTextToClipboard(textToCopy);
        });
    } else {
        fallbackCopyTextToClipboard(textToCopy);
    }
}

function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showCopySuccess();
        }
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
    }
    
    document.body.removeChild(textArea);
}

function showCopySuccess() {
    const copyButton = document.getElementById('copy-button');
    if (copyButton) {
        const originalText = copyButton.textContent;
        copyButton.textContent = '✓ Kopierat!';
        copyButton.style.background = '#28a745';
        
        setTimeout(() => {
            copyButton.textContent = originalText;
            copyButton.style.background = '#007bff';
        }, 2000);
    }
}

// Service worker registration
function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/sw.js').then(function(registration) {
                console.log('SW registered: ', registration);
            }).catch(function(registrationError) {
                console.log('SW registration failed: ', registrationError);
            });
        });
    }
}

// Cache clearing
function clearCaches() {
    if ('caches' in window) {
        caches.keys().then(function(names) {
            for (let name of names) {
                caches.delete(name);
            }
        });
    }
}

// Initialize admin functionality
document.addEventListener('DOMContentLoaded', function() {
    // Register service worker
    registerServiceWorker();
    
    // Set up event listeners for checkboxes
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            saveCheckboxState(this.id, this.checked);
            updateNextFasButton();
            updateDiploNextFasButton();
            updateStartButton();
        });
    });
    
    // Set up keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        if (event.key === 'F11') {
            event.preventDefault();
            toggleTimerMaximize();
        }
    });
    
    // Initialize test mode
    const testModeToggle = document.getElementById('test_mode_toggle');
    if (testModeToggle) {
        testModeToggle.addEventListener('change', toggleTestMode);
        toggleTestMode(); // Initial state
    }
});
