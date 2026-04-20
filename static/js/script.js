$(document).ready(function() {
    console.log('SoundGoodizer initialized');
    
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    $('[data-bs-toggle="popover"]').popover();
    
    
    $(document).on('click', '.add-to-cart-btn', function(e) {
        e.preventDefault();
        const instrumentId = $(this).data('instrument-id');
        addToCart(instrumentId);
    });
    
    
    $('#searchInput').on('input', debounce(function() {
        const searchTerm = $(this).val();
        if (searchTerm.length > 2) {
            performSearch(searchTerm);
        }
    }, 300));
    
    $('form').on('submit', function(e) {
        if (!validateForm(this)) {
            e.preventDefault();
        }
    });
    
    $('a[href^="#"]').on('click', function(e) {
        if ($(this).attr('href') !== '#') {
            e.preventDefault();
            const target = $(this).attr('href');
            if (target.length) {
                $('html, body').animate({
                    scrollTop: $(target).offset().top - 80
                }, 500);
            }
        }
    });
    
    setInterval(updateCartCount, 30000); 
});


function showNotification(message, type = 'info') {
    $('.custom-alert').remove();
    
    const alertHtml = `
        <div class="custom-alert alert alert-${type} alert-dismissible fade show position-fixed" 
             style="top: 100px; right: 20px; z-index: 9999; min-width: 300px;">
            <div class="d-flex align-items-center">
                <i class="bi ${getNotificationIcon(type)} me-2 fs-5"></i>
                <div>${message}</div>
                <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
            </div>
        </div>
    `;
    
    $('body').append(alertHtml);
    
    setTimeout(() => {
        $('.custom-alert').alert('close');
    }, 3000);
}

function getNotificationIcon(type) {
    switch(type) {
        case 'success': return 'bi-check-circle-fill';
        case 'warning': return 'bi-exclamation-triangle-fill';
        case 'danger': return 'bi-x-circle-fill';
        case 'info': return 'bi-info-circle-fill';
        default: return 'bi-info-circle-fill';
    }
}

function performSearch(term) {
    $.ajax({
        url: '/api/search',
        method: 'GET',
        data: { q: term },
        success: function(data) {
            console.log('Search results:', data);
        },
        error: function() {
            console.error('Search failed');
        }
    });
}

function validateForm(form) {
    let isValid = true;
    const $form = $(form);
    
    $form.find('[required]').each(function() {
        const $input = $(this);
        const value = $input.val().trim();
        
        if (!value) {
            $input.addClass('is-invalid');
            isValid = false;
        } else {
            $input.removeClass('is-invalid');
        }
        
        if ($input.attr('type') === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                $input.addClass('is-invalid');
                isValid = false;
            }
        }
    });
    
    return isValid;
}

function formatPrice(price) {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0
    }).format(price);
}

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

function loadCategories() {
    $.ajax({
        url: '/api/categories',
        method: 'GET',
        success: function(categories) {
            console.log('Categories loaded:', categories);
        },
        error: function() {
            console.error('Failed to load categories');
        }
    });
}

function initGallery() {
    $('.gallery-thumb').on('click', function() {
        const mainImage = $(this).data('main-image');
        if (mainImage) {
            $('#mainImage').attr('src', mainImage);
        }
        
        $('.gallery-thumb').removeClass('active');
        $(this).addClass('active');
    });
}

function initRating() {
    $('.rating-star').on('click', function() {
        const rating = $(this).data('rating');
        $('.rating-star').each(function() {
            if ($(this).data('rating') <= rating) {
                $(this).addClass('bi-star-fill').removeClass('bi-star');
            } else {
                $(this).removeClass('bi-star-fill').addClass('bi-star');
            }
        });
        
        $('#ratingInput').val(rating);
    });
}

function checkLocalStorage() {
    try {
        localStorage.setItem('test', 'test');
        localStorage.removeItem('test');
        return true;
    } catch (e) {
        return false;
    }
}

function saveToLocalStorage(key, value) {
    if (checkLocalStorage()) {
        localStorage.setItem(key, JSON.stringify(value));
    }
}

function loadFromLocalStorage(key) {
    if (checkLocalStorage()) {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    }
    return null;
}

function loadTheme() {
    const saved = localStorage.getItem('sg_theme') || 'light';
    applyTheme(saved, false);
}

function applyTheme(theme, save) {
    const html = document.getElementById('htmlRoot') || document.documentElement;
    html.setAttribute('data-bs-theme', theme);

    const iconNav = document.getElementById('themeIconNav');
    if (iconNav) {
        iconNav.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
    }

    if (save) localStorage.setItem('sg_theme', theme);
}

function toggleTheme() {
    const html = document.getElementById('htmlRoot') || document.documentElement;
    const current = html.getAttribute('data-bs-theme') || 'light';
    applyTheme(current === 'dark' ? 'light' : 'dark', true);
}
// ─────────────────────────────────────────────────────────────

loadTheme();
initGallery();
initRating();