// =========================================================
// Frana — Service Worker personnalisé
// =========================================================

const CACHE_VERSION = "frana-v1";
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;

// Ressources statiques à pré-cacher dès l'installation
const PRECACHE_URLS = [
    "/offline/",
    "/static/finances/img/logo.png",
    "/static/finances/img/pwa-icon-192.png",
    "/static/finances/img/pwa-icon-512.png",
    "/static/finances/img/pexels-pavel-danilyuk-7654180.jpg",
];

// =========================================================
// INSTALL — Précache les ressources essentielles
// =========================================================
self.addEventListener("install", (event) => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(STATIC_CACHE).then((cache) => {
            return cache.addAll(PRECACHE_URLS);
        })
    );
});

// =========================================================
// ACTIVATE — Nettoyer les anciens caches
// =========================================================
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter(
                        (name) =>
                            name.startsWith("frana-") &&
                            name !== STATIC_CACHE &&
                            name !== RUNTIME_CACHE
                    )
                    .map((name) => caches.delete(name))
            );
        })
    );
    return self.clients.claim();
});

// =========================================================
// FETCH — Stratégie adaptée selon le type de requête
// =========================================================
self.addEventListener("fetch", (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // 1) Ignorer les requêtes non-GET (POST, PUT, etc.)
    if (request.method !== "GET") return;

    // 2) Ignorer les requêtes vers d'autres domaines
    if (url.origin !== self.location.origin) return;

    // 3) Ignorer les URLs sensibles (admin, logout, etc.)
    if (
        url.pathname.startsWith("/admin/") ||
        url.pathname.startsWith("/deconnexion/") ||
        url.pathname.startsWith("/serviceworker.js")
    ) {
        return;
    }

    // 4) Fichiers statiques → Cache-first (rapide + efficace)
    if (url.pathname.startsWith("/static/") || url.pathname.startsWith("/media/")) {
        event.respondWith(
            caches.match(request).then((cached) => {
                return (
                    cached ||
                    fetch(request).then((response) => {
                        // Ne cacher que les réponses valides
                        if (response && response.status === 200) {
                            const clone = response.clone();
                            caches.open(STATIC_CACHE).then((cache) => {
                                cache.put(request, clone);
                            });
                        }
                        return response;
                    })
                );
            })
        );
        return;
    }

    // 5) Pages dynamiques → Network-first avec fallback offline
    event.respondWith(
        fetch(request)
            .then((response) => {
                // Optionnel : mettre en cache les pages HTML visitées
                if (
                    response &&
                    response.status === 200 &&
                    request.headers.get("accept")?.includes("text/html")
                ) {
                    const clone = response.clone();
                    caches.open(RUNTIME_CACHE).then((cache) => {
                        cache.put(request, clone);
                    });
                }
                return response;
            })
            .catch(() => {
                // En cas d'échec réseau, essayer le cache
                return caches.match(request).then((cached) => {
                    if (cached) return cached;
                    // Dernier recours : page offline
                    if (request.headers.get("accept")?.includes("text/html")) {
                        return caches.match("/offline/");
                    }
                });
            })
    );
});