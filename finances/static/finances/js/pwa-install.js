// =========================================================
// Frana — Installation PWA (bandeau incitatif, sitewide)
// =========================================================

(function () {
    const DISMISS_KEY = "frana_pwa_dismiss_until";
    const DISMISS_DAYS = 1; // ré-affiche le bandeau après ce délai si refusé

    // ---------------------------------------------------
    // 1) Enregistrement du Service Worker
    // ---------------------------------------------------
    if ("serviceWorker" in navigator) {
        window.addEventListener("load", () => {
            navigator.serviceWorker.register("/serviceworker.js")
                .then((reg) => console.log("Service Worker enregistré:", reg.scope))
                .catch((err) => console.error("Échec enregistrement Service Worker:", err));
        });
    }

    // ---------------------------------------------------
    // 2) Construction du bandeau (injecté en JS, pas de HTML à dupliquer)
    // ---------------------------------------------------
    function buildBanner() {
        const style = document.createElement("style");
        style.textContent = `
            #frana-pwa-banner {
                position: fixed;
                left: 50%;
                top: -160px;
                transform: translateX(-50%);
                width: min(92%, 460px);
                background: linear-gradient(135deg, #2a1c12, #1e140d);
                border: 1px solid rgba(217, 173, 85, 0.4);
                border-radius: 14px;
                box-shadow: 0 20px 50px rgba(0,0,0,0.5);
                padding: 18px 20px;
                display: flex;
                align-items: center;
                gap: 14px;
                z-index: 3000;
                font-family: Arial, sans-serif;
                transition: top 0.5s ease;
            }
            #frana-pwa-banner.show { top: 16px; }
            #frana-pwa-banner img {
                width: 46px; height: 46px; border-radius: 10px; flex-shrink: 0;
            }
            #frana-pwa-banner .frana-pwa-text { flex: 1; color: #f1e7d7; }
            #frana-pwa-banner .frana-pwa-text strong {
                display: block; font-size: 15px; margin-bottom: 2px; color: #f0ce82;
            }
            #frana-pwa-banner .frana-pwa-text span { font-size: 12.5px; opacity: 0.85; }
            #frana-pwa-banner .frana-pwa-actions {
                display: flex; flex-direction: column; gap: 6px; flex-shrink: 0;
            }
            #frana-pwa-install-btn {
                background: linear-gradient(90deg, #d9ad55, #f0ce82);
                color: #1e140d; border: none; border-radius: 8px;
                padding: 8px 16px; font-weight: 700; font-size: 13px;
                cursor: pointer; white-space: nowrap;
            }
            #frana-pwa-dismiss-btn {
                background: none; border: none; color: #cbbba4;
                font-size: 11.5px; cursor: pointer; text-decoration: underline;
            }
            @media (max-width: 500px) {
                #frana-pwa-banner { padding: 14px 16px; }
            }
        `;
        document.head.appendChild(style);

        const banner = document.createElement("div");
        banner.id = "frana-pwa-banner";
        banner.innerHTML = `
            <img src="/static/finances/img/pwa-icon-192.png" alt="Frana">
            <div class="frana-pwa-text">
                <strong>Installe Frana sur ton appareil</strong>
                <span>Accès plus rapide, notifications, et fonctionne même hors ligne.</span>
            </div>
            <div class="frana-pwa-actions">
                <button id="frana-pwa-install-btn">Installer</button>
                <button id="frana-pwa-dismiss-btn">Plus tard</button>
            </div>
        `;
        document.body.appendChild(banner);
        return banner;
    }

    // ---------------------------------------------------
    // 3) Logique d'affichage / installation / refus
    // ---------------------------------------------------
    let deferredPrompt = null;

    function isDismissed() {
        const until = localStorage.getItem(DISMISS_KEY);
        return until && Date.now() < parseInt(until, 10);
    }

    window.addEventListener("beforeinstallprompt", (e) => {
        e.preventDefault();
        deferredPrompt = e;

        if (isDismissed()) return;

        const banner = buildBanner();

        // léger délai pour laisser la page se charger avant de "pousser"
        setTimeout(() => banner.classList.add("show"), 1200);

        document.getElementById("frana-pwa-install-btn").addEventListener("click", async () => {
            banner.classList.remove("show");
            if (!deferredPrompt) return;
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            console.log("Résultat installation:", outcome);
            deferredPrompt = null;
            setTimeout(() => banner.remove(), 500);
        });

        document.getElementById("frana-pwa-dismiss-btn").addEventListener("click", () => {
            banner.classList.remove("show");
            localStorage.setItem(DISMISS_KEY, Date.now() + DISMISS_DAYS * 86400000);
            setTimeout(() => banner.remove(), 500);
        });
    });

    window.addEventListener("appinstalled", () => {
        deferredPrompt = null;
        const banner = document.getElementById("frana-pwa-banner");
        if (banner) banner.remove();
        console.log("PWA installée");
    });
})();