document.addEventListener("DOMContentLoaded", () => {
    const burger = document.getElementById("franaBurger");
    const closeBtn = document.getElementById("franaMobileClose");
    const overlay = document.getElementById("franaMobileMenu");
    const discoverBtn = document.getElementById("franaDiscoverBtn");

    if (!burger || !overlay) return;

    function openMenu() {
        overlay.classList.add("open");
        document.body.style.overflow = "hidden";
    }

    function closeMenu() {
        overlay.classList.remove("open");
        document.body.style.overflow = "";
    }

    burger.addEventListener("click", openMenu);
    if (closeBtn) closeBtn.addEventListener("click", closeMenu);
    if (discoverBtn) discoverBtn.addEventListener("click", closeMenu);

    overlay.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", closeMenu);
    });
});