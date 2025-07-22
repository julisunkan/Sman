// SocialMarket - Main JavaScript File

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Initialize file upload handlers
    initializeFileUploads();
    
    // Initialize copy to clipboard functionality
    initializeCopyToClipboard();
    
    // Initialize auto-dismiss alerts
    initializeAutoAlerts();
    
    // Initialize scroll to top functionality
    initializeScrollToTop();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize price formatting
    initializePriceFormatting();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

// Form validation enhancements
function initializeFormValidations() {
    // Add real-time validation feedback
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
        
        // Real-time validation for specific fields (throttled to prevent blinking)
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            let validationTimeout;
            input.addEventListener('input', function() {
                // Skip validation for support forms to prevent blinking
                if (this.closest('form').action && this.closest('form').action.includes('support')) {
                    return;
                }
                
                clearTimeout(validationTimeout);
                validationTimeout = setTimeout(() => {
                    if (this.checkValidity()) {
                        this.classList.remove('is-invalid');
                        this.classList.add('is-valid');
                    } else {
                        this.classList.remove('is-valid');
                        this.classList.add('is-invalid');
                    }
                }, 500); // Delay validation to prevent blinking
            });
        });
    });
    
    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('input', function() {
            const email = this.value;
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if (email && !emailRegex.test(email)) {
                this.setCustomValidity('Please enter a valid email address');
            } else {
                this.setCustomValidity('');
            }
        });
    });
    
    // Password strength validation
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        if (input.name === 'password' || input.id === 'password') {
            input.addEventListener('input', function() {
                const password = this.value;
                const strength = checkPasswordStrength(password);
                updatePasswordStrengthIndicator(this, strength);
            });
        }
    });
}

// Password strength checker
function checkPasswordStrength(password) {
    let score = 0;
    const checks = {
        length: password.length >= 8,
        lowercase: /[a-z]/.test(password),
        uppercase: /[A-Z]/.test(password),
        numbers: /\d/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };
    
    Object.values(checks).forEach(check => {
        if (check) score++;
    });
    
    if (score < 3) return 'weak';
    if (score < 5) return 'medium';
    return 'strong';
}

// Update password strength indicator
function updatePasswordStrengthIndicator(input, strength) {
    let indicator = input.parentNode.querySelector('.password-strength');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'password-strength mt-1';
        input.parentNode.appendChild(indicator);
    }
    
    const colors = {
        weak: 'danger',
        medium: 'warning',
        strong: 'success'
    };
    
    const messages = {
        weak: 'Weak password',
        medium: 'Medium strength',
        strong: 'Strong password'
    };
    
    indicator.innerHTML = `<small class="text-${colors[strength]}"><i class="fas fa-shield-alt me-1"></i>${messages[strength]}</small>`;
}

// File upload handlers
function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                // Check file type
                const allowedTypes = this.accept ? this.accept.split(',').map(type => type.trim()) : [];
                if (allowedTypes.length > 0) {
                    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
                    const isValidType = allowedTypes.some(type => 
                        type === fileExtension || 
                        file.type.startsWith(type.replace('*', ''))
                    );
                    
                    if (!isValidType) {
                        showAlert('Invalid file type. Please select a valid file.', 'danger');
                        this.value = '';
                        return;
                    }
                }
                
                // Show file size info and compression notice for large files
                const fileSizeKB = file.size / 1024;
                const maxSizeKB = 15;
                
                if (fileSizeKB > maxSizeKB && file.type.startsWith('image/')) {
                    showAlert(`Large file detected (${fileSizeKB.toFixed(1)}KB). It will be automatically compressed during upload.`, 'info');
                } else if (fileSizeKB > maxSizeKB && file.type === 'application/pdf') {
                    showAlert(`Large PDF detected (${fileSizeKB.toFixed(1)}KB). PDFs over ${maxSizeKB}KB are accepted but may take longer to process.`, 'info');
                }
                
                // Show file preview for images
                if (file.type.startsWith('image/')) {
                    showImagePreview(this, file);
                }
                
                // Update file input label
                updateFileInputLabel(this, file.name);
            }
        });
    });
}

// Show image preview
function showImagePreview(input, file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        let preview = input.parentNode.querySelector('.image-preview');
        
        if (!preview) {
            preview = document.createElement('div');
            preview.className = 'image-preview mt-2';
            input.parentNode.appendChild(preview);
        }
        
        preview.innerHTML = `
            <img src="${e.target.result}" class="img-thumbnail" style="max-width: 200px; max-height: 200px;">
            <div class="mt-1">
                <small class="text-muted">${file.name} (${formatFileSize(file.size)})</small>
            </div>
        `;
    };
    reader.readAsDataURL(file);
}

// Update file input label
function updateFileInputLabel(input, fileName) {
    const label = input.parentNode.querySelector('.form-label');
    if (label) {
        const originalText = label.getAttribute('data-original-text') || label.textContent;
        if (!label.getAttribute('data-original-text')) {
            label.setAttribute('data-original-text', originalText);
        }
        label.innerHTML = `${originalText} <small class="text-success">(${fileName})</small>`;
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Copy to clipboard functionality
function initializeCopyToClipboard() {
    const copyButtons = document.querySelectorAll('[data-copy]');
    
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy') || this.textContent;
            
            if (navigator.clipboard) {
                navigator.clipboard.writeText(textToCopy).then(() => {
                    showToast('Copied to clipboard!', 'success');
                    animateCopyButton(this);
                });
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = textToCopy;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                showToast('Copied to clipboard!', 'success');
                animateCopyButton(this);
            }
        });
    });
}

// Animate copy button
function animateCopyButton(button) {
    const originalHTML = button.innerHTML;
    button.innerHTML = '<i class="fas fa-check"></i>';
    button.classList.add('btn-success');
    
    setTimeout(() => {
        button.innerHTML = originalHTML;
        button.classList.remove('btn-success');
    }, 1500);
}

// Auto-dismiss alerts
function initializeAutoAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
}

// Scroll to top functionality
function initializeScrollToTop() {
    // Create scroll to top button
    const scrollButton = document.createElement('button');
    scrollButton.innerHTML = '<i class="fas fa-chevron-up"></i>';
    scrollButton.className = 'btn btn-primary position-fixed bottom-0 end-0 m-4 rounded-circle scroll-to-top';
    scrollButton.style.cssText = 'z-index: 1000; width: 50px; height: 50px; display: none;';
    document.body.appendChild(scrollButton);
    
    // Show/hide button based on scroll position
    window.addEventListener('scroll', function() {
        if (window.scrollY > 300) {
            scrollButton.style.display = 'block';
        } else {
            scrollButton.style.display = 'none';
        }
    });
    
    // Scroll to top when clicked
    scrollButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Search functionality enhancements
function initializeSearch() {
    const searchInputs = document.querySelectorAll('input[type="search"], .search-input');
    
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    performSearch(query, this);
                }, 300);
            }
        });
    });
}

// Perform search (placeholder - can be extended for specific search functionality)
function performSearch(query, input) {
    // This can be extended for real-time search functionality
    console.log('Searching for:', query);
}

// Price formatting
function initializePriceFormatting() {
    const priceInputs = document.querySelectorAll('input[name*="price"], input[name*="amount"]');
    
    priceInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                this.value = value.toFixed(2);
            }
        });
        
        input.addEventListener('input', function() {
            // Remove non-numeric characters except decimal point
            this.value = this.value.replace(/[^0-9.]/g, '');
            
            // Ensure only one decimal point
            const parts = this.value.split('.');
            if (parts.length > 2) {
                this.value = parts[0] + '.' + parts.slice(1).join('');
            }
        });
    });
}

// Utility function to show alerts
function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.alert-container') || document.body;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alert.style.cssText = 'z-index: 9999; max-width: 500px;';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

// Utility function to show toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `position-fixed top-0 end-0 m-3 alert alert-${type} alert-dismissible fade show`;
    toast.style.cssText = 'z-index: 9999; min-width: 250px;';
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentNode) {
            const bsAlert = new bootstrap.Alert(toast);
            bsAlert.close();
        }
    }, 3000);
}

// Format numbers for display
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Format currency for display
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-NG', {
        style: 'currency',
        currency: 'NGN'
    }).format(amount);
}

// Debounce function for performance
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Loading spinner utility
function showLoading(element) {
    const originalContent = element.innerHTML;
    element.setAttribute('data-original-content', originalContent);
    element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    element.disabled = true;
}

function hideLoading(element) {
    const originalContent = element.getAttribute('data-original-content');
    if (originalContent) {
        element.innerHTML = originalContent;
        element.removeAttribute('data-original-content');
    }
    element.disabled = false;
}

// Confirm action utility
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Initialize smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Global error handler for AJAX requests
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
});

// Export utilities for use in other scripts
window.SocialMarket = {
    showAlert,
    showToast,
    formatNumber,
    formatCurrency,
    debounce,
    showLoading,
    hideLoading,
    confirmAction
};
