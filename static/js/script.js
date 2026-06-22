$(document).ready(function() {
    $('[data-bs-toggle="tooltip"]').tooltip();
    $('[data-bs-toggle="popover"]').popover();

    $(document).on('click', '.add-to-cart-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const instrumentId = $(this).data('instrument-id');
        const instrumentName = $(this).data('instrument-name') || '';

        if (instrumentName !== '') {
            showAddTypeModal(instrumentId, instrumentName);
        } else {
            addToCartAjax(instrumentId, $(this));
        }
        return false;
    });

    $('#searchInput').on('input', debounce(function() {
        const searchTerm = $(this).val();
        if (searchTerm.length > 2) {
            performSearch(searchTerm);
        }
    }, 300));

    $(document).on('submit', 'form', function(e) {
        if (!validateForm(this)) {
            e.preventDefault();
            this.dataset.submitCancelled = '1';
            var form = this;
            setTimeout(function() { delete form.dataset.submitCancelled; }, 50);
            return;
        }
        delete this.dataset.submitCancelled;
        setFormLoading(this, true);
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

function addToCartAjax(instrumentId, $btn) {
    const originalHtml = $btn.html();
    $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status"></span>');

    $.ajax({
        url: '/api/add_to_cart',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ instrument_id: instrumentId }),
        success: function(data) {
            if (data.success) {
                showNotification(data.message, 'success');
                updateCartBadge(data.cart_count);
            } else if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                showNotification(data.message || 'Ошибка добавления в корзину', 'danger');
            }
        },
        error: function(xhr, status, err) {
            console.error('Cart AJAX error:', xhr.status, status, err, xhr.responseText);
            if (xhr.status === 401) {
                window.location.href = '/login';
            } else {
                showNotification('Ошибка соединения с сервером (' + xhr.status + ')', 'danger');
            }
        },
        complete: function() {
            $btn.prop('disabled', false).html(originalHtml);
        }
    });
}

function showAddTypeModal(instrumentId, instrumentName) {
    const existing = document.getElementById('addTypeModal');
    if (existing) existing.remove();

    const modalHtml = `
    <div class="modal fade" id="addTypeModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content border-0 shadow-lg rounded-4 overflow-hidden">

                <!-- Шаг 1: выбор типа -->
                <div id="stepChoose">
                    <div class="modal-header border-0 pb-0 pt-4 px-4">
                        <div>
                            <h5 class="modal-title fw-bold mb-1">Добавить в корзину</h5>
                            <p class="text-muted small mb-0" id="modalInstrumentNameStep1" style="max-width:320px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"></p>
                        </div>
                        <button type="button" class="btn-close ms-auto" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body px-4 py-4">
                        <div class="row g-3">
                            <div class="col-6">
                                <button id="addTypeBuyBtn"
                                    class="btn w-100 h-100 d-flex flex-column align-items-center justify-content-center gap-2 py-4 rounded-3"
                                    style="background:#f0f6ff;border:2px solid #c6deff;color:#1a4fa0;transition:all .2s;">
                                    <i class="bi bi-cart-plus" style="font-size:2rem;"></i>
                                    <span class="fw-semibold">Купить</span>
                                    <span class="small text-muted fw-normal">Добавить в корзину</span>
                                </button>
                            </div>
                            <div class="col-6">
                                <button id="addTypeRentBtn"
                                    class="btn w-100 h-100 d-flex flex-column align-items-center justify-content-center gap-2 py-4 rounded-3"
                                    style="background:#f0fbff;border:2px solid #b8e8ff;color:#0a6e9e;transition:all .2s;">
                                    <i class="bi bi-calendar-check" style="font-size:2rem;"></i>
                                    <span class="fw-semibold">Аренда</span>
                                    <span class="small text-muted fw-normal">Выбрать даты</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Шаг 2: выбор дат аренды -->
                <div id="stepRental" style="display:none;">
                    <div class="modal-header border-0 pb-0 pt-4 px-4">
                        <div>
                            <button class="btn btn-sm btn-link text-muted p-0 mb-1" id="backToChoose">
                                <i class="bi bi-arrow-left me-1"></i>Назад
                            </button>
                            <h5 class="modal-title fw-bold mb-1">Аренда</h5>
                            <p class="text-muted small mb-0" id="modalInstrumentNameStep2" style="max-width:320px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"></p>
                        </div>
                        <button type="button" class="btn-close ms-auto" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body px-4 py-3">
                        <div class="row g-3 mb-3">
                            <div class="col-6">
                                <label class="form-label fw-semibold small">Дата начала</label>
                                <input type="date" class="form-control" id="catalogRentalStart">
                            </div>
                            <div class="col-6">
                                <label class="form-label fw-semibold small">Дата окончания</label>
                                <input type="date" class="form-control" id="catalogRentalEnd">
                            </div>
                        </div>
                        <div class="bg-light rounded-3 p-3">
                            <div class="d-flex justify-content-between small mb-1">
                                <span class="text-muted">Цена за день:</span>
                                <span class="fw-semibold" id="catalogDailyPrice">—</span>
                            </div>
                            <div class="d-flex justify-content-between small mb-1">
                                <span class="text-muted">Количество дней:</span>
                                <span class="fw-semibold" id="catalogRentalDays">—</span>
                            </div>
                            <hr class="my-2">
                            <div class="d-flex justify-content-between">
                                <span class="fw-semibold">Итого:</span>
                                <span class="fw-bold text-primary" id="catalogRentalTotal">—</span>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer border-0 px-4 pb-4 pt-0">
                        <button type="button" class="btn btn-primary w-100 py-2 rounded-3 fw-semibold" id="catalogAddRentalBtn">
                            <i class="bi bi-calendar-plus me-2"></i>Добавить в корзину
                        </button>
                    </div>
                </div>

            </div>
        </div>
    </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    const modalEl = document.getElementById('addTypeModal');
    const modal = new bootstrap.Modal(modalEl);

    document.getElementById('modalInstrumentNameStep1').textContent = instrumentName;
    document.getElementById('modalInstrumentNameStep2').textContent = instrumentName;

    document.getElementById('addTypeBuyBtn').addEventListener('click', function() {
        modal.hide();
        const $btn = $('[data-instrument-id="' + instrumentId + '"].add-to-cart-btn').first();
        addToCartAjax(instrumentId, $btn.length ? $btn : $('<button>'));
    });

    document.getElementById('addTypeRentBtn').addEventListener('click', function() {
        document.getElementById('stepChoose').style.display = 'none';
        document.getElementById('stepRental').style.display = '';

        const today = new Date();
        const tomorrow = new Date(today); tomorrow.setDate(today.getDate() + 1);
        const nextWeek = new Date(today); nextWeek.setDate(today.getDate() + 7);
        const fmt = d => d.toISOString().split('T')[0];

        const startInput = document.getElementById('catalogRentalStart');
        const endInput = document.getElementById('catalogRentalEnd');
        startInput.min = fmt(tomorrow);
        endInput.min = fmt(tomorrow);
        startInput.value = fmt(tomorrow);
        endInput.value = fmt(nextWeek);

        fetch('/api/instrument_rental_price/' + instrumentId)
            .then(r => r.json())
            .then(data => {
                window._catalogRentalPrice = data.price || 0;
                document.getElementById('catalogDailyPrice').textContent =
                    parseFloat(data.price).toLocaleString('ru-RU') + ' ₽/день';
                updateRentalCalc();
            })
            .catch(() => {
                window._catalogRentalPrice = 0;
            });
    });

    document.getElementById('backToChoose').addEventListener('click', function() {
        document.getElementById('stepRental').style.display = 'none';
        document.getElementById('stepChoose').style.display = '';
    });

    function updateRentalCalc() {
        const start = document.getElementById('catalogRentalStart').value;
        const end = document.getElementById('catalogRentalEnd').value;
        const price = window._catalogRentalPrice || 0;
        if (!start || !end) return;
        const days = Math.ceil((new Date(end) - new Date(start)) / 86400000);
        if (days <= 0) return;
        document.getElementById('catalogRentalDays').textContent = days + ' дн.';
        document.getElementById('catalogRentalTotal').textContent =
            (price * days).toLocaleString('ru-RU') + ' ₽';
    }

    document.getElementById('catalogRentalStart').addEventListener('change', updateRentalCalc);
    document.getElementById('catalogRentalEnd').addEventListener('change', updateRentalCalc);

    document.getElementById('catalogAddRentalBtn').addEventListener('click', function() {
        const start = document.getElementById('catalogRentalStart').value;
        const end = document.getElementById('catalogRentalEnd').value;

        if (!start || !end) {
            showNotification('Выберите даты аренды', 'warning');
            return;
        }
        if (new Date(end) <= new Date(start)) {
            showNotification('Дата окончания должна быть позже даты начала', 'warning');
            return;
        }

        fetch('/add_to_rental_cart', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({instrument_id: instrumentId, rental_start: start, rental_end: end, quantity: 1})
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                modal.hide();
                if (typeof updateCartCount === 'function') updateCartCount();
                showNotification('Добавлено в корзину для аренды', 'success');
            } else if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                showNotification(data.message || 'Ошибка', 'danger');
            }
        })
        .catch(() => showNotification('Ошибка соединения', 'danger'));
    });

    modalEl.addEventListener('hidden.bs.modal', function() {
        modalEl.remove();
    });

    modal.show();
}

function updateCartBadge(count) {
    const $badge = $('#cartBadge');
    if (!$badge.length) return;

    $badge.text(count);
    if (count > 0) {
        $badge.removeClass('d-none');
    } else {
        $badge.addClass('d-none');
    }
}

function setFormLoading(form, loading) {
    const $form = $(form);
    const $submitBtns = $form.find('[type="submit"]');

    if (loading) {
        $submitBtns.each(function() {
            const $btn = $(this);
            $btn.data('original-html', $btn.html());
            $btn.prop('disabled', true).html(
                '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Загрузка...'
            );
        });
    } else {
        $submitBtns.each(function() {
            const $btn = $(this);
            const original = $btn.data('original-html');
            if (original) $btn.html(original);
            $btn.prop('disabled', false);
        });
    }
}

window.addEventListener('pageshow', function(e) {
    if (e.persisted) {
        $('form [type="submit"]').each(function() {
            const $btn = $(this);
            const original = $btn.data('original-html');
            if (original) $btn.html(original);
            $btn.prop('disabled', false);
        });
    }
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
        case 'danger':  return 'bi-x-circle-fill';
        case 'info':    return 'bi-info-circle-fill';
        default:        return 'bi-info-circle-fill';
    }
}

function performSearch(term) {
    $.ajax({
        url: '/api/search',
        method: 'GET',
        data: { q: term },
        success: function(data) {},
        error: function() {}
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
        success: function(categories) {},
        error: function() {}
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

loadTheme();
initGallery();
initRating();
