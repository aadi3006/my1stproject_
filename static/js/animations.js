/* ============================================================
   MEDICARE — STITCH-INSPIRED ANIMATIONS & INTERACTIONS
   Tropical particles, playful wobble, teal/coral sparkles
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
    initScrollReveal();
    initStatCounters();
    initCardTilt();
    initRippleEffect();
    initSidebar();
    initTropicalParticles();
});

/* ---------- Scroll Reveal ---------- */
function initScrollReveal() {
    const reveals = document.querySelectorAll('.reveal');
    if (!reveals.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -40px 0px'
    });

    reveals.forEach(el => observer.observe(el));
}

/* ---------- Animated Stat Counters ---------- */
function initStatCounters() {
    const counters = document.querySelectorAll('[data-count]');
    if (!counters.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(el => observer.observe(el));
}

function animateCounter(el) {
    const target = parseInt(el.dataset.count, 10);
    const duration = 1400;
    const step = Math.ceil(target / (duration / 16));
    let current = 0;

    const update = () => {
        current += step;
        if (current >= target) {
            el.textContent = target;
            // Bounce effect on completion
            el.style.transform = 'scale(1.15)';
            setTimeout(() => { el.style.transform = 'scale(1)'; }, 200);
            return;
        }
        el.textContent = current;
        requestAnimationFrame(update);
    };

    requestAnimationFrame(update);
}

/* ---------- 3D Card Tilt (Playful) ---------- */
function initCardTilt() {
    const cards = document.querySelectorAll('.stat-card, .action-card, .db-table-card');

    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = ((y - centerY) / centerY) * -6;
            const rotateY = ((x - centerX) / centerX) * 6;

            card.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
        });
    });
}

/* ---------- Ripple Effect on Buttons ---------- */
function initRippleEffect() {
    const buttons = document.querySelectorAll('.btn');

    buttons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();

            ripple.style.cssText = `
                position: absolute;
                width: 0; height: 0;
                border-radius: 50%;
                background: rgba(255,255,255,0.35);
                transform: translate(-50%, -50%);
                left: ${e.clientX - rect.left}px;
                top: ${e.clientY - rect.top}px;
                animation: rippleAnim 0.6s ease-out forwards;
                pointer-events: none;
            `;

            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    });

    // Add the ripple animation CSS
    if (!document.getElementById('ripple-css')) {
        const style = document.createElement('style');
        style.id = 'ripple-css';
        style.textContent = `
            @keyframes rippleAnim {
                to {
                    width: 300px;
                    height: 300px;
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

/* ---------- Sidebar Toggle ---------- */
function initSidebar() {
    const toggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (!toggle || !sidebar) return;

    toggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        if (overlay) overlay.classList.toggle('active');
    });

    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }
}

/* ---------- Tropical Particles (Teal/Coral/Gold sparkles) ---------- */
function initTropicalParticles() {
    const bg = document.querySelector('.app-bg');
    if (!bg) return;

    const colors = [
        'rgba(255, 107, 107, 0.22)',   // coral
        'rgba(168, 85, 247, 0.18)',    // violet
        'rgba(245, 166, 35, 0.20)',    // gold
        'rgba(61, 214, 160, 0.15)',    // mint
        'rgba(255, 176, 136, 0.16)',   // peach
    ];

    for (let i = 0; i < 25; i++) {
        const particle = document.createElement('div');
        const size = Math.random() * 4 + 1;
        const x = Math.random() * 100;
        const delay = Math.random() * 20;
        const duration = Math.random() * 18 + 14;
        const color = colors[Math.floor(Math.random() * colors.length)];
        const drift = Math.random() > 0.5 ? Math.floor(Math.random() * 60) : -Math.floor(Math.random() * 60);

        particle.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            background: ${color};
            border-radius: 50%;
            left: ${x}%;
            bottom: -10px;
            animation: tropicalFloat ${duration}s ${delay}s infinite linear;
            pointer-events: none;
            box-shadow: 0 0 ${size * 2}px ${color};
        `;

        bg.appendChild(particle);
    }

    // Float-up animation with horizontal drift
    if (!document.getElementById('particle-css')) {
        const style = document.createElement('style');
        style.id = 'particle-css';
        style.textContent = `
            @keyframes tropicalFloat {
                0% {
                    transform: translateY(0) translateX(0) scale(0);
                    opacity: 0;
                }
                5% {
                    transform: translateY(-5vh) translateX(5px) scale(1);
                    opacity: 0.8;
                }
                50% {
                    opacity: 0.4;
                }
                100% {
                    transform: translateY(-105vh) translateX(${Math.random() > 0.5 ? '' : '-'}${30 + Math.random() * 40}px) scale(0.3);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

/* ---------- Live Billing Calculator ---------- */
function initBillingCalc() {
    const inputs = document.querySelectorAll('.calc-input');
    const totalDisplay = document.getElementById('total-display');
    if (!inputs.length || !totalDisplay) return;

    inputs.forEach(input => {
        input.addEventListener('input', () => {
            let total = 0;
            inputs.forEach(i => {
                total += parseFloat(i.value) || 0;
            });
            animateTotalChange(totalDisplay, total);
        });
    });
}

function animateTotalChange(el, newVal) {
    el.textContent = '₹' + newVal.toFixed(2);
    el.style.transform = 'scale(1.12)';
    el.style.color = 'var(--accent-coral)';
    setTimeout(() => {
        el.style.transform = 'scale(1)';
    }, 200);
}

// Expose for use in billing page
window.initBillingCalc = initBillingCalc;

/* ---------- DB Explorer: Client-Side Search & Sort ---------- */
function initDBSearch() {
    const searchInput = document.getElementById('db-search-input');
    const table = document.getElementById('db-data-table');
    if (!searchInput || !table) return;

    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query) ? '' : 'none';
        });
    });
}

function initDBSort() {
    const table = document.getElementById('db-data-table');
    if (!table) return;

    const headers = table.querySelectorAll('th.sortable');

    headers.forEach((header, colIdx) => {
        header.addEventListener('click', () => {
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const isAsc = header.classList.contains('sort-asc');

            // Clear all sort classes
            headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));

            // Toggle direction
            header.classList.add(isAsc ? 'sort-desc' : 'sort-asc');
            const direction = isAsc ? -1 : 1;

            rows.sort((a, b) => {
                const cellA = a.cells[colIdx]?.textContent.trim() || '';
                const cellB = b.cells[colIdx]?.textContent.trim() || '';

                // Try numeric comparison first
                const numA = parseFloat(cellA);
                const numB = parseFloat(cellB);
                if (!isNaN(numA) && !isNaN(numB)) {
                    return (numA - numB) * direction;
                }

                return cellA.localeCompare(cellB) * direction;
            });

            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

window.initDBSearch = initDBSearch;
window.initDBSort = initDBSort;
