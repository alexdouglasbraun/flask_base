(function () {
    const storageKey = "theme-preference";
    const root = document.documentElement;
    const toggle = document.getElementById("theme-toggle");

    function getPreferredTheme() {
        const savedTheme = localStorage.getItem(storageKey);
        if (savedTheme === "light" || savedTheme === "dark") {
            return savedTheme;
        }

        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }

    function updateToggleLabel(theme) {
        if (!toggle) {
            return;
        }

        const icon = toggle.querySelector(".theme-toggle-icon");
        const label = toggle.querySelector(".theme-toggle-label");

        if (theme === "dark") {
            icon.textContent = "D";
            label.textContent = "Dark";
        } else {
            icon.textContent = "L";
            label.textContent = "Light";
        }
    }

    function applyTheme(theme) {
        root.setAttribute("data-bs-theme", theme);
        root.style.colorScheme = theme;
        localStorage.setItem(storageKey, theme);
        updateToggleLabel(theme);
    }

    applyTheme(getPreferredTheme());

    if (!toggle) {
        return;
    }

    toggle.addEventListener("click", function () {
        const nextTheme = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
        applyTheme(nextTheme);
    });
})();
