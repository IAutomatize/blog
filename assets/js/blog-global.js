// ========================================
// IAUTOMATIZE - BLOG GLOBAL JS
// Scripts globais para um Blog de Notícias
// ========================================

// ===== CONSTANTES E VARIÁVEIS GLOBAIS =====
const DOM = {
    progressBar: document.getElementById('progressBar'),
    mainHeader: document.getElementById('mainHeader'),
    mobileMenuBtn: document.getElementById('mobileMenuBtn'),
    mobileMenu: document.getElementById('mobileMenu'),
    navLinks: document.querySelectorAll('.nav-link'),
    mobileNavLinks: document.querySelectorAll('.mobile-nav-link'),
    // Elementos que podem ser animados ao rolar (ex: imagens, blocos de texto)
    animatedElements: document.querySelectorAll('.fade-in-on-scroll')
};

// ===== FUNÇÕES UTILITÁRIAS =====

// Debounce para otimizar performance em eventos de scroll
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

// Smooth scroll para links internos
function smoothScroll(targetElement, duration = 800) {
    // Garante que o targetElement é um elemento DOM
    if (!targetElement || typeof targetElement.getBoundingClientRect !== 'function') {
        console.warn("smoothScroll: Elemento alvo inválido.");
        return;
    }

    // Calcula a posição do alvo, considerando o header fixo
    const headerOffset = DOM.mainHeader ? DOM.mainHeader.offsetHeight + 10 : 0; // +10px de margem
    const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - headerOffset;
    const startPosition = window.pageYOffset;
    const distance = targetPosition - startPosition;
    let startTime = null;

    function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        // Função de easing (aceleração/desaceleração)
        const ease = (t, b, c, d) => {
            t /= d / 2;
            if (t < 1) return c / 2 * t * t + b;
            t--;
            return -c / 2 * (t * (t - 2) - 1) + b;
        };
        const run = ease(timeElapsed, startPosition, distance, duration);
        window.scrollTo(0, run);
        if (timeElapsed < duration) requestAnimationFrame(animation);
    }

    requestAnimationFrame(animation);
}

// ===== PROGRESS BAR DE LEITURA =====
function updateProgressBar() {
    const documentHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const scrollPosition = document.documentElement.scrollTop || document.body.scrollTop;
    
    if (DOM.progressBar) {
        const scrolledPercentage = (scrollPosition / documentHeight) * 100;
        DOM.progressBar.style.width = scrolledPercentage + '%';
    }
}

// ===== HEADER SCROLL EFFECT =====
function handleHeaderScroll() {
    if (DOM.mainHeader) {
        if (window.scrollY > 50) { // Se o scroll for maior que 50px
            DOM.mainHeader.classList.add('scrolled');
        } else {
            DOM.mainHeader.classList.remove('scrolled');
        }
    }
}

// ===== NAVEGAÇÃO ATIVA =====
function updateActiveNavLink() {
    const sections = document.querySelectorAll('section[id]');
    const scrollY = window.pageYOffset;
    const headerHeight = DOM.mainHeader ? DOM.mainHeader.offsetHeight : 0;

    sections.forEach(section => {
        const sectionTop = section.offsetTop - headerHeight - 10; // Ajuste para o header e um pequeno offset
        const sectionBottom = sectionTop + section.offsetHeight;
        const sectionId = section.getAttribute('id');

        if (scrollY >= sectionTop && scrollY < sectionBottom) {
            // Remove 'active' de todos os links
            DOM.navLinks.forEach(link => link.classList.remove('active'));
            DOM.mobileNavLinks.forEach(link => link.classList.remove('active'));

            // Adiciona 'active' ao link correspondente
            const activeLink = document.querySelector(`.nav-link[href="#${sectionId}"]`);
            const activeMobileLink = document.querySelector(`.mobile-nav-link[href="#${sectionId}"]`);
            if (activeLink) {
                activeLink.classList.add('active');
            }
            if (activeMobileLink) {
                activeMobileLink.classList.add('active');
            }
        }
    });
}

// ===== MOBILE MENU =====
function toggleMobileMenu() {
    if (DOM.mobileMenuBtn && DOM.mobileMenu) {
        DOM.mobileMenuBtn.classList.toggle('active');
        DOM.mobileMenu.classList.toggle('active');
        
        // Atualiza ARIA para acessibilidade
        const isExpanded = DOM.mobileMenuBtn.classList.contains('active');
        DOM.mobileMenuBtn.setAttribute('aria-expanded', isExpanded);
        document.body.style.overflow = isExpanded ? 'hidden' : ''; // Evita scroll do body quando menu aberto
    }
}

function closeMobileMenu() {
    if (DOM.mobileMenuBtn && DOM.mobileMenu) {
        DOM.mobileMenuBtn.classList.remove('active');
        DOM.mobileMenu.classList.remove('active');
        DOM.mobileMenuBtn.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = ''; // Restaura scroll do body
    }
}

// ===== INTERSECTION OBSERVER PARA ANIMAÇÕES =====
function setupIntersectionObserver() {
    if (DOM.animatedElements.length === 0) return;

    const options = {
        threshold: 0.1, // Elemento visível em 10%
        rootMargin: '0px 0px -50px 0px' // Começa a animar 50px antes do fim da tela
    };
    
    const observer = new IntersectionObserver((entries, observerSelf) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observerSelf.unobserve(entry.target); // Para de observar após animar
            }
        });
    }, options);
    
    DOM.animatedElements.forEach(element => {
        observer.observe(element);
    });
}

// ===== ANALYTICS E TRACKING (Exemplo) =====
// Esta função é um placeholder. Você a conectaria ao seu sistema de analytics (ex: Google Analytics).
function trackEvent(category, action, label) {
    if (typeof gtag === 'undefined') {
        // console.warn('gtag (Google Analytics) não encontrado. O evento não será rastreado.');
        return;
    }
    // Exemplo de como você chamaria o Google Analytics
    gtag('event', action, {
        event_category: category,
        event_label: label
    });
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    // Eventos de scroll (debounce para melhor performance)
    window.addEventListener('scroll', debounce(() => {
        updateProgressBar();
        handleHeaderScroll();
        updateActiveNavLink();
    }, 10)); // Executa a cada 10ms (apenas se houver scroll)
    
    // Mobile menu
    if (DOM.mobileMenuBtn) {
        DOM.mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    }
    
    // Navegação suave para links internos
    [...DOM.navLinks, ...DOM.mobileNavLinks].forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            // Verifica se é um link para uma seção interna (começa com # e não é apenas '#')
            if (href && href.startsWith('#') && href.length > 1) {
                e.preventDefault(); // Previne o comportamento padrão do link
                const targetSection = document.querySelector(href);
                
                if (targetSection) {
                    smoothScroll(targetSection); // Scroll suave
                    closeMobileMenu(); // Fecha o menu mobile após clicar em um link
                    trackEvent('Navigation', 'Click', href); // Rastreia o clique
                }
            }
        });
    });
    
    // Fechar menu mobile ao clicar fora
    document.addEventListener('click', (e) => {
        if (DOM.mobileMenu && DOM.mobileMenuBtn &&
            !DOM.mobileMenu.contains(e.target) && 
            !DOM.mobileMenuBtn.contains(e.target) && 
            DOM.mobileMenu.classList.contains('active')) {
            closeMobileMenu();
        }
    });
    
    // Tecla ESC fecha o menu mobile
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && DOM.mobileMenu && DOM.mobileMenu.classList.contains('active')) {
            closeMobileMenu();
        }
    });

    // Exemplo de rastreamento para links de CTA (se houver no blog)
    const ctaLinks = document.querySelectorAll('.btn-cta');
    ctaLinks.forEach(btn => {
        btn.addEventListener('click', () => {
            trackEvent('CTA', 'Click', btn.textContent.trim());
        });
    });
}

// ===== LAZY LOAD DE IMAGENS (se você usar data-src) =====
function lazyLoadImages() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    if (img.dataset.srcset) {
                        img.srcset = img.dataset.srcset;
                    }
                    img.removeAttribute('data-src');
                    img.removeAttribute('data-srcset');
                    observer.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback simples para navegadores antigos
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
            if (img.dataset.srcset) {
                img.srcset = img.dataset.srcset;
            }
            img.removeAttribute('data-src');
            img.removeAttribute('data-srcset');
        });
    }
}

// ===== INICIALIZAÇÃO GERAL =====
function init() {
    // Inicializa observadores de animação (para elementos como imagens de artigos ou seções)
    setupIntersectionObserver();
    
    // Configura todos os event listeners
    setupEventListeners();
    
    // Aplica lazy loading para imagens marcadas
    lazyLoadImages();
    
    // Define o estado inicial da barra de progresso e header
    updateProgressBar();
    handleHeaderScroll();
    updateActiveNavLink();
    
    // Adiciona classe ao body para indicar que JS está habilitado (para CSS condicional)
    document.body.classList.add('js-enabled');
    
    console.log('IAUTOMATIZE Blog Global - Scripts carregados com sucesso! 🚀');
}

// Garante que o DOM esteja completamente carregado antes de inicializar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init(); // Se já estiver carregado, inicializa imediatamente
}

// ===== SERVICE WORKER (para PWA futuro, se aplicar ao blog) =====
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').then(
            registration => console.log('ServiceWorker registrado:', registration.scope),
            err => console.log('ServiceWorker falhou:', err)
        );
    });
}

// Exporta funções úteis para acesso global, se necessário
window.IAutomatizeBlog = {
    trackEvent,
    smoothScroll
};

// Função para filtrar artigos por categoria
function filterArticlesByCategory() {
  // Verificar se existe um parâmetro 'categoria' na URL
  const urlParams = new URLSearchParams(window.location.search);
  const category = urlParams.get('categoria');
  
  if (!category) return; // Se não há categoria, mostra todos os artigos
  
  // Atualizar título da seção
  const newsTitle = document.querySelector('#ultimas-noticias .section-title');
  if (newsTitle) {
    newsTitle.innerHTML = `Artigos: <span class="category-highlight">${decodeURIComponent(category).replace(/-/g, ' ')}</span>`;
  }
  
  // Selecionar todos os cards de artigos
  const articleCards = document.querySelectorAll('.article-card');
  
  // Contador de artigos visíveis
  let visibleCount = 0;
  
  // Filtrar artigos
  articleCards.forEach(card => {
    // Obter categoria do artigo (podemos adicionar um data-attribute ou buscar no texto)
    // Esta é uma implementação simplificada - pode precisar ser adaptada
    const articleCategory = card.querySelector('.article-meta')?.textContent.toLowerCase() || '';
    const normalizedCategory = category.toLowerCase().replace(/-/g, ' ');
    
    if (articleCategory.includes(normalizedCategory)) {
      card.style.display = 'block';
      visibleCount++;
    } else {
      card.style.display = 'none';
    }
  });
  
  // Mensagem se não houver artigos
  if (visibleCount === 0) {
    const articlesContainer = document.querySelector('#recent-articles-container');
    if (articlesContainer) {
      const noArticlesMsg = document.createElement('div');
      noArticlesMsg.className = 'no-articles-message';
      noArticlesMsg.innerHTML = `<p>Nenhum artigo encontrado na categoria "${decodeURIComponent(category).replace(/-/g, ' ')}". <a href="/">Ver todos</a></p>`;
      articlesContainer.appendChild(noArticlesMsg);
    }
  }
}

// Adicionar CSS correspondente
const categoryStyles = document.createElement('style');
categoryStyles.textContent = `
  .category-highlight {
    color: var(--primary);
    font-weight: bold;
  }
  
  .no-articles-message {
    background: var(--dark-lighter);
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    margin: 20px 0;
  }
`;
document.head.appendChild(categoryStyles);

// Executar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', filterArticlesByCategory);
