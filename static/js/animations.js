
class AnimationHandler {
    constructor() {
        this.animatedElements = [];
        this.init();
    }

    init() {
        this.addScrollAnimations();
        this.addHoverEffects();
        this.addButtonAnimations();
        this.addChartAnimations();
        this.startParticleEffects();
    }

    addScrollAnimations() {
        // animation class to elements that should animate on scroll
        const animateElements = document.querySelectorAll('.animate-on-scroll');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        animateElements.forEach(element => observer.observe(element));
    }

    addHoverEffects() {
        //  hover animations to cards
        const cards = document.querySelectorAll('.feature-card, .stat-card, .chart-card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-10px)';
                card.style.boxShadow = 'var(--shadow-xl)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
                card.style.boxShadow = 'var(--shadow-lg)';
            });
        });

        //  hover animations to buttons
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(btn => {
            btn.addEventListener('mouseenter', () => {
                btn.style.transform = 'translateY(-3px)';
            });
            
            btn.addEventListener('mouseleave', () => {
                btn.style.transform = 'translateY(0)';
            });
        });
    }

    addButtonAnimations() {
        //  ripple effect to buttons
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                const ripple = document.createElement('span');
                const rect = button.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.cssText = `
                    position: absolute;
                    border-radius: 50%;
                    background: rgba(255, 255, 255, 0.7);
                    transform: scale(0);
                    animation: ripple-animation 0.6s linear;
                    width: ${size}px;
                    height: ${size}px;
                    left: ${x}px;
                    top: ${y}px;
                `;
                
                button.appendChild(ripple);
                setTimeout(() => ripple.remove(), 600);
            });
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
    }

    addChartAnimations() {
        // Animate chart elements when they appear
        const charts = document.querySelectorAll('.chart-container');
        charts.forEach(chart => {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const bars = chart.querySelectorAll('.chart-bar');
                        bars.forEach((bar, index) => {
                            setTimeout(() => {
                                bar.style.transform = 'scaleY(1)';
                                bar.style.opacity = '1';
                            }, index * 100);
                        });
                    }
                });
            }, { threshold: 0.5 });
            
            observer.observe(chart);
        });
    }

    startParticleEffects() {
        // Create floating particles in hero section
        const heroSection = document.querySelector('.hero');
        if (!heroSection) return;

        for (let i = 0; i < 20; i++) {
            this.createParticle(heroSection);
        }
    }

    createParticle(container) {
        const particle = document.createElement('div');
        particle.innerHTML = '<i class="fas fa-circle"></i>';
        particle.style.cssText = `
            position: absolute;
            color: rgba(16, 185, 129, 0.1);
            font-size: ${Math.random() * 10 + 5}px;
            top: ${Math.random() * 100}%;
            left: ${Math.random() * 100}%;
            animation: float-particle ${Math.random() * 20 + 10}s infinite ease-in-out;
            z-index: -1;
        `;
        
        container.appendChild(particle);
        
        
        setTimeout(() => {
            particle.remove();
            
            if (container.parentElement) {
                this.createParticle(container);
            }
        }, (Math.random() * 20 + 10) * 1000);
    }

    addCounterAnimations() {
        // Animate number counters
        const counters = document.querySelectorAll('.counter');
        counters.forEach(counter => {
            const target = parseInt(counter.getAttribute('data-target'));
            const increment = target / 100;
            let current = 0;
            
            const updateCounter = () => {
                if (current < target) {
                    current += increment;
                    counter.textContent = Math.floor(current);
                    setTimeout(updateCounter, 20);
                } else {
                    counter.textContent = target;
                }
            };
            
            const observer = new IntersectionObserver((entries) => {
                if (entries[0].isIntersecting) {
                    updateCounter();
                    observer.unobserve(counter);
                }
            });
            
            observer.observe(counter);
        });
    }

    addTypingAnimation() {
        
        const messages = document.querySelectorAll('.message.ai-message');
        messages.forEach(message => {
            const text = message.querySelector('.message-text');
            if (!text) return;
            
            const originalText = text.textContent;
            text.textContent = '';
            
            let i = 0;
            const typingInterval = setInterval(() => {
                if (i < originalText.length) {
                    text.textContent += originalText.charAt(i);
                    i++;
                } else {
                    clearInterval(typingInterval);
                }
            }, 20);
        });
    }

    addConfettiEffect() {
        
        const celebrateBtn = document.querySelector('.celebrate-btn');
        if (!celebrateBtn) return;

        celebrateBtn.addEventListener('click', () => {
            this.createConfetti();
        });
    }

    createConfetti() {
        const colors = ['#10B981', '#34D399', '#059669', '#A7F3D0', '#065F46'];
        const confettiCount = 100;
        
        for (let i = 0; i < confettiCount; i++) {
            const confetti = document.createElement('div');
            confetti.innerHTML = '<i class="fas fa-star"></i>';
            confetti.style.cssText = `
                position: fixed;
                top: -10px;
                left: ${Math.random() * 100}vw;
                color: ${colors[Math.floor(Math.random() * colors.length)]};
                font-size: ${Math.random() * 20 + 10}px;
                animation: confetti-fall ${Math.random() * 3 + 2}s linear forwards;
                z-index: 9999;
                opacity: ${Math.random() * 0.7 + 0.3};
            `;
            
            document.body.appendChild(confetti);
            
            setTimeout(() => confetti.remove(), 5000);
        }
        
       
        const style = document.createElement('style');
        style.textContent = `
            @keyframes confetti-fall {
                0% {
                    transform: translateY(0) rotate(0deg);
                }
                100% {
                    transform: translateY(100vh) rotate(${Math.random() * 360}deg);
                }
            }
            
            @keyframes float-particle {
                0%, 100% {
                    transform: translateY(0) translateX(0);
                }
                50% {
                    transform: translateY(-20px) translateX(20px);
                }
            }
        `;
        document.head.appendChild(style);
    }
}


document.addEventListener('DOMContentLoaded', () => {
    window.animationHandler = new AnimationHandler();
});