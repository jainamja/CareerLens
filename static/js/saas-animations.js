document.addEventListener('DOMContentLoaded', () => {
    initAll();
});

// Re-init for HTMX
document.body.addEventListener('htmx:afterSwap', function() {
    initAll();
});

function initAll() {
    initStaggeredEntrances();
    initCountUp();
    initToasts();
    initSidebarIndicator();
}

// IntersectObserver for fade-up animations
function initStaggeredEntrances() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // If it has a delay class or we want to stagger children
                const element = entry.target;
                
                // Animate element itself
                if (element.classList.contains('animate-on-scroll')) {
                    element.classList.add('animate-fade-in-up');
                    element.classList.remove('opacity-0', 'animate-on-scroll');
                    observer.unobserve(element);
                }
                
                // Animate children (like grid cards)
                if (element.classList.contains('stagger-children')) {
                    const children = element.querySelectorAll('.stagger-item');
                    children.forEach((child, index) => {
                        // Max out delay classes at 400 or dynamically assign inline style delay
                        const delay = Math.min(index * 50, 400); 
                        child.style.animationDelay = `${delay}ms`;
                        child.classList.add('animate-fade-in-up');
                        child.classList.remove('opacity-0');
                    });
                    element.classList.remove('stagger-children');
                    observer.unobserve(element);
                }
            }
        });
    }, { rootMargin: '0px 0px -50px 0px', threshold: 0.1 });

    document.querySelectorAll('.animate-on-scroll, .stagger-children').forEach(el => {
        observer.observe(el);
    });
}

// Count Up Animation for Stats
function initCountUp() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = parseInt(el.getAttribute('data-count-to'), 10) || 0;
                
                // Respect reduced motion
                const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
                if (prefersReducedMotion || target === 0) {
                    el.innerText = target;
                    el.classList.remove('count-up-pending');
                    observer.unobserve(el);
                    return;
                }

                const duration = 1000; // 1s
                const start = performance.now();
                
                function updateNumber(time) {
                    const elapsed = time - start;
                    const progress = Math.min(elapsed / duration, 1);
                    // easeOutQuart
                    const ease = 1 - Math.pow(1 - progress, 4);
                    
                    el.innerText = Math.floor(ease * target);
                    
                    if (progress < 1) {
                        requestAnimationFrame(updateNumber);
                    } else {
                        el.innerText = target;
                    }
                }
                requestAnimationFrame(updateNumber);
                
                el.classList.remove('count-up-pending');
                observer.unobserve(el);
            }
        });
    }, { rootMargin: '0px', threshold: 0.1 });

    document.querySelectorAll('.count-up-pending').forEach(el => observer.observe(el));
}

function initToasts() {
    const toasts = document.querySelectorAll('.saas-toast:not(.initialized)');
    toasts.forEach(toast => {
        toast.classList.add('initialized');
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            dismissToast(toast);
        }, 5000);
        
        // Click to dismiss
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => dismissToast(toast));
        }
    });
}

function dismissToast(toast) {
    if (toast.classList.contains('toast-exit')) return;
    toast.classList.remove('toast-enter');
    toast.classList.add('toast-exit');
    setTimeout(() => {
        toast.remove();
    }, 300); // match animation duration
}

function initSidebarIndicator() {
    const indicator = document.getElementById('sidebar-active-indicator');
    if (!indicator) return;

    const nav = document.getElementById('sidebar-nav');
    if (!nav) return;

    const activeLink = nav.querySelector('.active-sidebar-link');
    
    function updateIndicator(link) {
        if (!link) {
            indicator.style.opacity = '0';
            return;
        }
        
        // Ensure nav is relative for indicator absolute positioning
        const navRect = nav.getBoundingClientRect();
        const linkRect = link.getBoundingClientRect();
        
        // Calculate relative position
        const offsetTop = linkRect.top - navRect.top;
        
        indicator.style.opacity = '1';
        indicator.style.height = `${linkRect.height * 0.7}px`;
        indicator.style.transform = `translateY(${offsetTop + (linkRect.height * 0.15)}px)`;
    }

    if (activeLink) {
        // slight delay to ensure layout is done
        setTimeout(() => updateIndicator(activeLink), 50);
        
        // Update on resize
        window.addEventListener('resize', () => updateIndicator(nav.querySelector('.active-sidebar-link')));
    } else {
        indicator.style.opacity = '0';
    }
}
