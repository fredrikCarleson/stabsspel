/**
 * Admin JavaScript functionality for Stabsspel
 * Extracted from inline scripts for better organization
 */

// Time adjustment modal functionality
function openTimeAdjustmentModal(spelId) {
    const modal = document.getElementById('timeAdjustmentModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeTimeAdjustmentModal() {
    const modal = document.getElementById('timeAdjustmentModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById('timeAdjustmentModal');
    if (event.target === modal) {
        closeTimeAdjustmentModal();
    }
}

// Timer functionality
function openTimerWindow(spelId) {
    // Hämta aktuell tid och status från admin-timern
    var timerElement = document.getElementById('timer');
    var statusElement = document.querySelector('.badge');
    
    var currentTime = timerElement ? timerElement.textContent : '10:00';
    var currentStatus = statusElement ? statusElement.textContent.toLowerCase().replace('status: ', '') : 'paused';
    
    // Debug: log the status for troubleshooting
    console.log('Timer element:', timerElement);
    console.log('Status element:', statusElement);
    console.log('Current time:', currentTime);
    console.log('Current status:', currentStatus);
    
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
    // Extract spel_id from current URL
    const currentPath = window.location.pathname;
    const pathParts = currentPath.split('/');
    const spelId = pathParts[2]; // Assuming URL structure is /admin/{spel_id}/...
    
    fetch(`/admin/${spelId}/save_checkbox`, {
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
    const nextFasButton = document.getElementById('next-fas-btn');
    
    if (nextFasButton) {
        nextFasButton.disabled = !allChecked;
        nextFasButton.style.opacity = allChecked ? '1' : '0.5';
    }
}

function updateDiploNextFasButton() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    const nextFasButton = document.getElementById('diplo-next-fas-btn');
    
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

// Auto-fill functionality is handled inline in the HTML template
// to ensure proper backend communication

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

// ============================================================================
// ANIMATION FUNCTIONS - SPELIFIERING
// ============================================================================

/**
 * Trigger score increase animation
 * @param {string} elementId - ID of the element to animate
 */
function animateScoreIncrease(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('score-increase');
        void element.offsetWidth; // Trigger reflow
        element.classList.add('score-increase');
        
        // Remove class after animation completes
        setTimeout(() => {
            element.classList.remove('score-increase');
        }, 600);
    }
}

/**
 * Trigger score decrease animation
 * @param {string} elementId - ID of the element to animate
 */
function animateScoreDecrease(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('score-decrease');
        void element.offsetWidth; // Trigger reflow
        element.classList.add('score-decrease');
        
        // Remove class after animation completes
        setTimeout(() => {
            element.classList.remove('score-decrease');
        }, 600);
    }
}

/**
 * Trigger news headline animation
 * @param {string} elementId - ID of the element to animate
 * @param {boolean} isBreaking - Whether this is breaking news
 */
function animateNewsHeadline(elementId, isBreaking = false) {
    const element = document.getElementById(elementId);
    if (element) {
        // Add breaking news class if specified
        if (isBreaking) {
            element.classList.add('breaking');
        }
        
        element.classList.remove('news-appear');
        void element.offsetWidth; // Trigger reflow
        element.classList.add('news-appear');
        
        // Remove class after animation completes
        setTimeout(() => {
            element.classList.remove('news-appear');
        }, 800);
    }
}

/**
 * Trigger timer tick animation
 * @param {string} elementId - ID of the timer element
 */
function animateTimerTick(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('timer-tick');
        void element.offsetWidth; // Trigger reflow
        element.classList.add('timer-tick');
        
        // Remove class after animation completes
        setTimeout(() => {
            element.classList.remove('timer-tick');
        }, 300);
    }
}

/**
 * Trigger pulse animation for important elements
 * @param {string} elementId - ID of the element to animate
 */
function animatePulse(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('pulse');
        
        // Remove class after animation completes
        setTimeout(() => {
            element.classList.remove('pulse');
        }, 2000);
    }
}

/**
 * Trigger shake animation for errors/warnings
 * @param {string} elementId - ID of the element to animate
 */
function animateShake(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('shake');
        void element.offsetWidth; // Trigger reflow
        element.classList.add('shake');
        
        // Remove class after animation completes
        setTimeout(() => {
            element.classList.remove('shake');
        }, 600);
    }
}

/**
 * Trigger bounce animation for success
 * @param {string} elementId - ID of the element to animate
 */
function animateBounce(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('bounce');
        void element.offsetWidth; // Trigger reflow
        element.classList.add('bounce');
        
        // Remove class after animation completes
        setTimeout(() => {
            element.classList.remove('bounce');
        }, 1000);
    }
}

// ============================================================================
// TEAM COLOR UTILITIES
// ============================================================================

/**
 * Apply team color to an element
 * @param {string} elementId - ID of the element
 * @param {string} teamName - Team name (alfa, bravo, stt, fm, bs, media, sapo, regeringen, usa)
 * @param {string} type - Type of color (text, background, border, button)
 */
function applyTeamColor(elementId, teamName, type = 'text') {
    const element = document.getElementById(elementId);
    if (element) {
        // Remove existing team classes
        element.classList.remove(
            'team-alfa', 'team-bravo', 'team-stt', 'team-fm', 'team-bs', 
            'team-media', 'team-sapo', 'team-regeringen', 'team-usa',
            'team-bg-alfa', 'team-bg-bravo', 'team-bg-stt', 'team-bg-fm', 'team-bg-bs',
            'team-bg-media', 'team-bg-sapo', 'team-bg-regeringen', 'team-bg-usa',
            'team-border-alfa', 'team-border-bravo', 'team-border-stt', 'team-border-fm', 'team-border-bs',
            'team-border-media', 'team-border-sapo', 'team-border-regeringen', 'team-border-usa',
            'btn-team-alfa', 'btn-team-bravo', 'btn-team-stt', 'btn-team-fm', 'btn-team-bs',
            'btn-team-media', 'btn-team-sapo', 'btn-team-regeringen', 'btn-team-usa'
        );
        
        // Add appropriate team class
        switch (type) {
            case 'text':
                element.classList.add(`team-${teamName}`);
                break;
            case 'background':
                element.classList.add(`team-bg-${teamName}`);
                break;
            case 'border':
                element.classList.add(`team-border-${teamName}`);
                break;
            case 'button':
                element.classList.add(`btn-team-${teamName}`);
                break;
        }
    }
}

/**
 * Create team indicator element
 * @param {string} teamName - Team name
 * @returns {HTMLElement} - Team indicator element
 */
function createTeamIndicator(teamName) {
    const indicator = document.createElement('span');
    indicator.className = `team-indicator ${teamName}`;
    return indicator;
}

// ============================================================================
// DRAMATIC TYPOGRAPHY UTILITIES
// ============================================================================

/**
 * Apply dramatic typography to an element
 * @param {string} elementId - ID of the element
 * @param {string} type - Type of dramatic styling (dramatic, condensed, emphasis)
 */
function applyDramaticTypography(elementId, type = 'dramatic') {
    const element = document.getElementById(elementId);
    if (element) {
        // Remove existing dramatic classes
        element.classList.remove('text-dramatic', 'text-condensed', 'text-emphasis');
        
        // Add appropriate class
        switch (type) {
            case 'dramatic':
                element.classList.add('text-dramatic');
                break;
            case 'condensed':
                element.classList.add('text-condensed');
                break;
            case 'emphasis':
                element.classList.add('text-emphasis');
                break;
        }
    }
}

/**
 * Create news headline element
 * @param {string} text - Headline text
 * @param {boolean} isBreaking - Whether this is breaking news
 * @returns {HTMLElement} - News headline element
 */
function createNewsHeadline(text, isBreaking = false) {
    const headline = document.createElement('div');
    headline.className = 'news-headline';
    if (isBreaking) {
        headline.classList.add('breaking');
    }
    headline.textContent = text;
    return headline;
}

/**
 * Create phase title element
 * @param {string} text - Phase title text
 * @param {string} phase - Phase type (order, diplomati, result)
 * @returns {HTMLElement} - Phase title element
 */
function createPhaseTitle(text, phase = 'order') {
    const title = document.createElement('h2');
    title.className = 'phase-title';
    if (phase === 'result') {
        title.classList.add('result');
    }
    title.textContent = text;
    return title;
}

// ============================================================================
// AUTO-ANIMATION TRIGGERS
// ============================================================================

/**
 * Set up automatic animation triggers
 */
function setupAnimationTriggers() {
    // Monitor score changes
    const scoreElements = document.querySelectorAll('[data-score]');
    scoreElements.forEach(element => {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'data-score') {
                    const oldValue = mutation.oldValue;
                    const newValue = element.getAttribute('data-score');
                    
                    if (oldValue && newValue) {
                        const oldScore = parseInt(oldValue);
                        const newScore = parseInt(newValue);
                        
                        if (newScore > oldScore) {
                            animateScoreIncrease(element.id);
                        } else if (newScore < oldScore) {
                            animateScoreDecrease(element.id);
                        }
                    }
                }
            });
        });
        
        observer.observe(element, {
            attributes: true,
            attributeOldValue: true
        });
    });
    
    // Monitor timer changes
    const timerElement = document.getElementById('timer');
    if (timerElement) {
        let lastTime = timerElement.textContent;
        
        const timerObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' || mutation.type === 'characterData') {
                    const currentTime = timerElement.textContent;
                    if (currentTime !== lastTime) {
                        animateTimerTick('timer');
                        lastTime = currentTime;
                    }
                }
            });
        });
        
        timerObserver.observe(timerElement, {
            childList: true,
            characterData: true,
            subtree: true
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

    // Initialize animations when DOM is loaded
    setupAnimationTriggers();
    
    // Apply team colors to existing elements
    const teamElements = document.querySelectorAll('[data-team]');
    teamElements.forEach(element => {
        const teamName = element.getAttribute('data-team');
        const colorType = element.getAttribute('data-color-type') || 'text';
        applyTeamColor(element.id, teamName, colorType);
    });
    
    // Apply dramatic typography to existing elements
    const dramaticElements = document.querySelectorAll('[data-dramatic]');
    dramaticElements.forEach(element => {
        const dramaticType = element.getAttribute('data-dramatic');
        applyDramaticTypography(element.id, dramaticType);
    });
});

// Apply data-driven widths/colors for progress bars
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.progress-fill').forEach(function (el) {
    const w = el.getAttribute('data-width');
    const c = el.getAttribute('data-color');
    if (w) el.style.width = (parseFloat(w) || 0) + '%';
    if (c) el.style.backgroundColor = c;
  });

  // Apply inline-like status badge styles via data-style
  document.querySelectorAll('.status-badge[data-style]').forEach(function (el) {
    const s = el.getAttribute('data-style');
    if (!s) return;
    s.split(';').forEach(function (rule) {
      const [prop, val] = rule.split(':');
      if (prop && val) el.style[prop.trim()] = val.trim();
    });
  });

  // Apply quarter pill dynamic colors/borders
  document.querySelectorAll('.quarter-pill').forEach(function (el) {
    const bg = el.getAttribute('data-bg');
    const fg = el.getAttribute('data-fg');
    const border = el.getAttribute('data-border');
    if (bg) el.style.backgroundColor = bg;
    if (fg) el.style.color = fg;
    if (border) el.style.border = border;
  });
});