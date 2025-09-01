// Основний JavaScript файл для веб-інтерфейсу Twitter Bot

// Клієнтський кеш для зменшення кількості API запитів
const clientCache = {
    data: {},
    timestamps: {},
    ttl: 30000, // збільшено з 10 до 30 секунд в мілісекундах
    
    set: function(key, value) {
        this.data[key] = value;
        this.timestamps[key] = Date.now();
    },
    
    get: function(key) {
        const timestamp = this.timestamps[key];
        if (!timestamp) return null;
        
        if (Date.now() - timestamp > this.ttl) {
            delete this.data[key];
            delete this.timestamps[key];
            return null;
        }
        
        return this.data[key];
    },
    
    invalidate: function(key) {
        delete this.data[key];
        delete this.timestamps[key];
    },
    
    clear: function() {
        this.data = {};
        this.timestamps = {};
    }
};

// Функція для очищення кешу при оновленні даних
function clearClientCache() {
    clientCache.clear();
    console.log('Клієнтський кеш очищено');
}

// Функція для кешованих API запитів
async function cachedFetch(url, options = {}) {
    const cacheKey = url + (options.body ? JSON.stringify(options.body) : '');
    
    // Перевіряємо кеш
    const cached = clientCache.get(cacheKey);
    if (cached) {
        return cached;
    }
    
    try {
        const response = await fetch(url, options);
        const data = await response.json();
        
        // Кешуємо результат
        clientCache.set(cacheKey, data);
        return data;
    } catch (error) {
        console.error('API запит не вдався:', error);
        throw error;
    }
}

// Функції для навігації
function toggleSidebar() {
    document.body.classList.toggle('sidebar-collapsed');
}

function closeMobileMenu() {
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenu) {
        mobileMenu.classList.remove('active');
    }
}

// Функція для відкриття/закриття мобільного меню
function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenu) {
        mobileMenu.classList.toggle('active');
    }
}

// Функція для оновлення статусу системи
function updateSystemStatus() {
    cachedFetch('/api/status')
        .then(data => {
            const indicator = document.getElementById('status-indicator');
            const text = document.getElementById('status-text');
            
            if (indicator && text) {
                if (data.system_running) {
                    indicator.className = 'status-indicator running';
                    text.textContent = 'Працює';
                } else {
                    indicator.className = 'status-indicator stopped';
                    text.textContent = 'Зупинено';
                }
            }
        })
        .catch(error => {
            console.error('Помилка оновлення статусу:', error);
        });
}

// Функція для показу сповіщень
function showNotification(message, type = 'info') {
    // Створюємо елемент сповіщення
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()" title="Закрити">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Додаємо сповіщення на сторінку
    document.body.appendChild(notification);
    
    // Автоматично видаляємо через 10 секунд (збільшено з 5 до 10)
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 10000);
}

// Функція для форматування часу
function formatTimeAgo(timestamp) {
    if (!timestamp) return 'Невідомо';
    
    const now = new Date();
    const date = new Date(timestamp);
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'щойно';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} хв тому`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} год тому`;
    if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} дн тому`;
    
    return date.toLocaleDateString('uk-UA');
}

// Функція для форматування uptime
function formatUptime(milliseconds) {
    if (!milliseconds) return '00:00:00';
    
    const seconds = Math.floor(milliseconds / 1000);
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Функція для перевірки автентифікації
function checkAuth() {
    // Перевіряємо, чи користувач авторизований
    // Якщо ні - перенаправляємо на логін
    if (!document.cookie.includes('session=')) {
        window.location.href = '/login';
    }
}

// Ініціалізація при завантаженні сторінки
document.addEventListener('DOMContentLoaded', function() {
    // Запускаємо оновлення статусу кожні 30 секунд (збільшено з 10)
    setInterval(updateSystemStatus, 30000);
    
    // Початкове оновлення статусу
    updateSystemStatus();
    
    // Додаємо обробники для мобільного меню
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', toggleMobileMenu);
    }
    
    // Закриваємо мобільне меню при кліку поза ним
    document.addEventListener('click', function(event) {
        const mobileMenu = document.getElementById('mobile-menu');
        if (mobileMenu && !mobileMenu.contains(event.target) && !event.target.closest('.mobile-menu-toggle')) {
            closeMobileMenu();
        }
    });
});

// Експортуємо функції для використання в інших файлах
window.showNotification = showNotification;
window.formatTimeAgo = formatTimeAgo;
window.formatUptime = formatUptime;
window.toggleSidebar = toggleSidebar;
window.closeMobileMenu = closeMobileMenu;
window.toggleMobileMenu = toggleMobileMenu;
