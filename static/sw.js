const CACHE_NAME = 'myscheduler-v2';
const STATIC_ASSETS = [
  '/static/style.css',
  '/static/script.js',
  '/static/icon-192.png',
  '/static/icon-512.png',
  '/manifest.json',
  'https://unpkg.com/vue@3/dist/vue.global.js'
];

// 安装时缓存静态资源，立即激活
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// 激活时清除旧缓存
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

// 拦截请求，按类型选择不同缓存策略
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // 只处理 GET 请求
  if (event.request.method !== 'GET') return;

  // API 请求 → 网络优先，失败时返回缓存
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // HTML 导航请求（页面跳转）→ 网络优先，保证登录状态正确
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // 静态资源（CSS/JS/图片等）→ 缓存优先，未命中时从网络获取并缓存
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      });
    })
  );
});