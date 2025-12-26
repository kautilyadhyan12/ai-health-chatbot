
class Utils {
    static showAlert(message, type = 'info', duration = 5000) {
        const alertContainer = document.getElementById('alertContainer');
        if (!alertContainer) {
            console.warn('Alert container not found');
            return;
        }

        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `
            <i class="fas fa-${this.getAlertIcon(type)}"></i>
            <span>${message}</span>
            <button class="alert-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        
        const style = document.createElement('style');
        style.textContent = `
            .alert-close {
                background: none;
                border: none;
                color: inherit;
                cursor: pointer;
                margin-left: auto;
                opacity: 0.7;
                padding: 0.25rem;
                border-radius: 0.25rem;
            }
            .alert-close:hover {
                opacity: 1;
                background: rgba(255, 255, 255, 0.2);
            }
        `;
        alert.appendChild(style);

        alertContainer.appendChild(alert);

        if (duration > 0) {
            setTimeout(() => {
                if (alert.parentElement) {
                    alert.remove();
                }
            }, duration);
        }

        return alert;
    }

    static getAlertIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    static formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    static formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minutes ago`;
        if (diffHours < 24) return `${diffHours} hours ago`;
        if (diffDays < 7) return `${diffDays} days ago`;
        return this.formatDate(dateString);
    }

    static debounce(func, wait) {
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

    static showLoading(element, text = 'Loading...') {
        if (!element) return;

        const originalContent = element.innerHTML;
        element.dataset.originalContent = originalContent;
        element.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <span>${text}</span>
            </div>
        `;
        element.disabled = true;

        
        const style = document.createElement('style');
        style.textContent = `
            .loading {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: var(--gray-600);
            }
            .spinner {
                width: 20px;
                height: 20px;
                border: 2px solid var(--gray-300);
                border-top-color: var(--primary-color);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        element.appendChild(style);
    }

    static hideLoading(element) {
        if (!element || !element.dataset.originalContent) return;
        element.innerHTML = element.dataset.originalContent;
        element.disabled = false;
        delete element.dataset.originalContent;
    }

    static validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    static validatePassword(password) {
        return password.length >= 6;
    }

    static getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    static setCookie(name, value, days) {
        const expires = new Date(Date.now() + days * 864e5).toUTCString();
        document.cookie = `${name}=${value}; expires=${expires}; path=/`;
    }

    static removeCookie(name) {
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
    }
}


class APIService {
    static async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await response.json().catch(() => ({
                    error: `HTTP ${response.status}: ${response.statusText}`
                }));
                throw new Error(error.error || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    static async get(url) {
        return this.request(url, { method: 'GET' });
    }

    static async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async put(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
}

// Form Handlers
class FormHandler {
    static init() {
        
        const registerForm = document.getElementById('register-form');
        if (registerForm) {
            registerForm.addEventListener('submit', this.handleRegistration);
        }

        
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', this.handleLogin);
        }

       
        this.initFormValidation();
    }

    static handleRegistration = async (e) => {
        e.preventDefault();

        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');

        
        const formData = new FormData(form);
        const data = {
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password')
        };

        
        if (!data.username || !data.email || !data.password) {
            Utils.showAlert('Please fill in all fields', 'error');
            return;
        }

        if (!Utils.validateEmail(data.email)) {
            Utils.showAlert('Please enter a valid email address', 'error');
            return;
        }

        if (!Utils.validatePassword(data.password)) {
            Utils.showAlert('Password must be at least 6 characters', 'error');
            return;
        }

        try {
            Utils.showLoading(submitBtn, 'Creating account...');

            const result = await APIService.post('/register', data);

            if (result.message) {
                Utils.showAlert(result.message, 'success');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            } else if (result.error) {
                Utils.showAlert(result.error, 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            Utils.showAlert('Registration failed. Please try again.', 'error');
        } finally {
            Utils.hideLoading(submitBtn);
        }
    };

    static handleLogin = async (e) => {
        e.preventDefault();

        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');

        const formData = new FormData(form);
        const data = {
            username: formData.get('username'),
            password: formData.get('password')
        };

        
        if (!data.username || !data.password) {
            Utils.showAlert('Please fill in all fields', 'error');
            return;
        }

        try {
            Utils.showLoading(submitBtn, 'Logging in...');

            const result = await APIService.post('/login', data);

            if (result.message) {
                Utils.showAlert(result.message, 'success');

                
                setTimeout(() => {
                    if (typeof reconnectSocketAfterLogin === 'function') {
                        reconnectSocketAfterLogin();
                    }
                }, 100);

                setTimeout(() => {
                    window.location.href = result.redirect || '/dashboard';
                }, 1000);
            } else if (result.error) {
                Utils.showAlert(result.error, 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            Utils.showAlert('Login failed. Please check your credentials.', 'error');
        } finally {
            Utils.hideLoading(submitBtn);
        }
    };

    static initFormValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const requiredFields = form.querySelectorAll('[required]');
                let isValid = true;

                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        isValid = false;
                        field.classList.add('error');

                        // Add error message
                        if (!field.nextElementSibling?.classList.contains('error-message')) {
                            const errorMsg = document.createElement('div');
                            errorMsg.className = 'error-message';
                            errorMsg.textContent = 'This field is required';
                            errorMsg.style.cssText = `
                                color: var(--danger-color);
                                font-size: 0.75rem;
                                margin-top: 0.25rem;
                            `;
                            field.parentNode.appendChild(errorMsg);
                        }
                    } else {
                        field.classList.remove('error');
                        const errorMsg = field.nextElementSibling;
                        if (errorMsg?.classList.contains('error-message')) {
                            errorMsg.remove();
                        }
                    }
                });

                if (!isValid) {
                    e.preventDefault();
                    Utils.showAlert('Please fill in all required fields', 'error');
                }
            });

            
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('input', () => {
                    input.classList.remove('error');
                    const errorMsg = input.nextElementSibling;
                    if (errorMsg?.classList.contains('error-message')) {
                        errorMsg.remove();
                    }
                });
            });
        });
    }
}


class NavigationHandler {
    static init() {
        
        const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', () => {
                const navLinks = document.querySelector('.nav-links');
                if (navLinks) {
                    navLinks.style.display = navLinks.style.display === 'flex' ? 'none' : 'flex';
                }
            });
        }

        
        const navItems = document.querySelectorAll('.nav-item[data-section]');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.getAttribute('data-section');
                this.switchSection(section);

                
                navItems.forEach(navItem => navItem.classList.remove('active'));
                item.classList.add('active');

                
                this.updatePageTitle(section);
            });
        });

        
        const logoutBtn = document.querySelector('.logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                if (confirm('Are you sure you want to logout?')) {
                    try {
                        const result = await APIService.get('/logout');
                        if (result.message) {
                            Utils.showAlert(result.message, 'success');
                            setTimeout(() => {
                                window.location.href = result.redirect || '/';
                            }, 1000);
                        }
                    } catch (error) {
                        console.error('Logout error:', error);
                        window.location.href = '/';
                    }
                }
            });
        }

        
        const hash = window.location.hash.substring(1);
        if (hash) {
            this.switchSection(hash);
        }
    }

    static switchSection(section) {
        
        const sections = document.querySelectorAll('.content-section');
        sections.forEach(sec => {
            sec.classList.remove('active');
        });

        
        const targetSection = document.getElementById(`${section}Section`);
        if (targetSection) {
            targetSection.classList.add('active');
            window.location.hash = section;
        }
    }

    static updatePageTitle(section) {
        const titles = {
            dashboard: 'Dashboard',
            chat: 'AI Chat Assistant',
            
            history: 'Chat History',
            settings: 'Settings'
        };

        const pageTitle = document.getElementById('pageTitle');
        const pageSubtitle = document.getElementById('pageSubtitle');

        if (pageTitle) {
            pageTitle.textContent = titles[section] || 'Dashboard';
        }

        if (pageSubtitle) {
            const subtitles = {
                dashboard: 'Monitor your health interactions and get AI-powered insights',
                chat: 'Chat with your AI medical assistant powered by LLaMA-3 8B',
                
                history: 'View and manage your conversation history',
                settings: 'Manage your MedAI Assistant preferences and account details'
            };
            pageSubtitle.textContent = subtitles[section] || '';
        }
    }
}


document.addEventListener('DOMContentLoaded', () => {
    
    if (typeof AnimationHandler !== 'undefined') {
        window.animationHandler = new AnimationHandler();
    }
    
    
    addScrollAnimations();
    
    
    addHoverEffects();
    
  
    FormHandler.init();
    
   
    NavigationHandler.init();
    
    
    initTooltips();
    
   
    initAutoResizeTextareas();
    
   
    addErrorStyles();
});

function addScrollAnimations() {
    const elements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });
    
    elements.forEach(element => observer.observe(element));
}

function addHoverEffects() {
    
    const interactiveElements = document.querySelectorAll('.btn, .card, .feature-item, .stat-card');
    
    interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', () => {
            element.classList.add('hover-lift');
        });
        
        element.addEventListener('mouseleave', () => {
            element.classList.remove('hover-lift');
        });
    });
}


function initTooltips() {
   
    const tooltips = document.querySelectorAll('[title]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', (e) => {
            
        });
    });
}

function initAutoResizeTextareas() {
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
}

function addErrorStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .error {
            border-color: var(--danger-color) !important;
        }
        .error:focus {
            box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1) !important;
        }
    `;
    document.head.appendChild(style);
}

// Additional utility functions
function initTooltips() {
    const tooltips = document.querySelectorAll('[title]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', (e) => {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = e.target.title;
            tooltip.style.cssText = `
                position: absolute;
                background: var(--gray-900);
                color: white;
                padding: 0.5rem 0.75rem;
                border-radius: var(--radius-sm);
                font-size: 0.75rem;
                white-space: nowrap;
                z-index: 1000;
                pointer-events: none;
                transform: translateY(-100%);
                margin-top: -0.5rem;
            `;

            const rect = e.target.getBoundingClientRect();
            tooltip.style.left = `${rect.left + rect.width / 2}px`;
            tooltip.style.top = `${rect.top}px`;
            tooltip.style.transform = 'translate(-50%, -100%)';

            document.body.appendChild(tooltip);

            element.addEventListener('mouseleave', () => {
                tooltip.remove();
            }, { once: true });
        });
    });
}

function initAutoResizeTextareas() {
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
}

function addErrorStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .error {
            border-color: var(--danger-color) !important;
        }
        .error:focus {
            box-shadow: 0 0 0 3px rgba(245, 101, 101, 0.1) !important;
        }
    `;
    document.head.appendChild(style);
}

// ============================================
// MEDICAL ANIMATIONS 
// ============================================

class MedicalAnimations {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.addMedicalElements();
        this.startHeartbeatAnimation();
    }

    bindEvents() {
        
        const cards = document.querySelectorAll('.medical-card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.classList.add('pulse-glow');
            });
            card.addEventListener('mouseleave', () => {
                card.classList.remove('pulse-glow');
            });
        });

        
        const medicalBtns = document.querySelectorAll('.btn-medical');
        medicalBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.createRippleEffect(e, btn);
            });
        });

       
        const symptomTags = document.querySelectorAll('.symptom-tag');
        symptomTags.forEach(tag => {
            tag.addEventListener('click', () => {
                this.animateTag(tag);
            });
        });
    }

    createRippleEffect(event, element) {
        const ripple = document.createElement('span');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.7);
            transform: scale(0);
            animation: ripple-animation 0.6s linear;
            width: ${size}px;
            height: ${size}px;
            top: ${y}px;
            left: ${x}px;
            pointer-events: none;
        `;

        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    }

    animateTag(tag) {
        tag.style.transform = 'scale(0.95)';
        tag.style.backgroundColor = 'rgba(16, 185, 129, 0.2)';
        
        setTimeout(() => {
            tag.style.transform = 'scale(1)';
            tag.style.backgroundColor = '';
        }, 200);
    }

    addMedicalElements() {
        
        const healthIndicators = document.querySelectorAll('.health-indicator');
        healthIndicators.forEach(indicator => {
            indicator.classList.add('heartbeat');
        });

        
        const fadeElements = document.querySelectorAll('.chart-card, .stat-card');
        fadeElements.forEach((element, index) => {
            element.style.animationDelay = `${index * 0.1}s`;
            element.classList.add('animate__animated', 'animate__fadeInUp');
        });
    }

    startHeartbeatAnimation() {
        
        const healthMeters = document.querySelectorAll('.health-fill');
        healthMeters.forEach(meter => {
            const targetWidth = meter.style.width;
            meter.style.width = '0%';
            
            setTimeout(() => {
                meter.style.width = targetWidth;
            }, 300);
        });
    }

    
    showTypingAnimation(element) {
        const typing = document.createElement('div');
        typing.className = 'typing-medical';
        typing.innerHTML = '<span></span><span></span><span></span>';
        
        element.appendChild(typing);
        return typing;
    }
}


document.addEventListener('DOMContentLoaded', () => {
    window.medicalAnimations = new MedicalAnimations();
});


const style = document.createElement('style');
style.textContent = `
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);


window.Utils = Utils;
window.APIService = APIService;      

