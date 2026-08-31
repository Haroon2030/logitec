document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector(".sidebar-toggle");
    const label = toggle && toggle.querySelector(".toggle-label");
    const applySidebar = (collapsed) => {
        document.documentElement.classList.toggle("sidebar-collapsed", collapsed);
        localStorage.setItem("sidebar-collapsed", collapsed ? "1" : "0");
        if (!toggle) return;
        toggle.setAttribute("aria-expanded", String(!collapsed));
        toggle.setAttribute("aria-label", collapsed ? "توسيع القائمة" : "طي القائمة");
        toggle.title = collapsed ? "توسيع القائمة" : "طي القائمة";
        if (label) label.textContent = collapsed ? "توسيع القائمة" : "طي القائمة";
    };
    if (toggle) {
        applySidebar(document.documentElement.classList.contains("sidebar-collapsed"));
        toggle.addEventListener("click", () => {
            applySidebar(!document.documentElement.classList.contains("sidebar-collapsed"));
        });
    }

    document.querySelectorAll("[data-nav-group]").forEach((group) => {
        const btn = group.querySelector(".nav-parent");
        if (!btn) return;
        btn.addEventListener("click", () => {
            if (document.documentElement.classList.contains("sidebar-collapsed")) {
                applySidebar(false);
                group.classList.add("is-open");
                btn.setAttribute("aria-expanded", "true");
                return;
            }
            const open = group.classList.toggle("is-open");
            btn.setAttribute("aria-expanded", String(open));
        });
    });

    const openers = document.querySelectorAll("[data-open]");
    openers.forEach((btn) => {
        btn.addEventListener("click", () => {
            const modal = document.getElementById(btn.dataset.open);
            if (!modal) return;
            modal.hidden = false;
            modal.classList.add("is-open");
        });
    });

    document.querySelectorAll("[data-close]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const modal = btn.closest(".modal");
            if (!modal) return;
            modal.classList.remove("is-open");
            modal.hidden = true;
        });
    });

    const params = new URLSearchParams(window.location.search);
    if (params.get("new") === "1") {
        const modal = document.getElementById("create-modal");
        if (modal) {
            modal.hidden = false;
            modal.classList.add("is-open");
        }
    }

    const filterInput = document.getElementById("ship-filter");
    if (filterInput) {
        filterInput.addEventListener("input", () => {
            const q = filterInput.value.trim();
            document.querySelectorAll(".ship-card").forEach((card) => {
                card.hidden = q && !card.textContent.includes(q);
            });
        });
    }

    const cards = document.querySelectorAll(".ship-card, .slot[data-id]");
    const zones = document.querySelectorAll(".drop-zone");
    const form = document.getElementById("assign-form");
    cards.forEach((card) => {
        card.addEventListener("dragstart", (event) => {
            event.dataTransfer.setData("text/plain", card.dataset.id);
        });
    });
    zones.forEach((zone) => {
        zone.addEventListener("dragover", (event) => {
            event.preventDefault();
            zone.classList.add("is-over");
        });
        zone.addEventListener("dragleave", () => zone.classList.remove("is-over"));
        zone.addEventListener("drop", (event) => {
            event.preventDefault();
            zone.classList.remove("is-over");
            if (!form) return;
            document.getElementById("assign-shipment").value = event.dataTransfer.getData("text/plain");
            document.getElementById("assign-warehouse").value = zone.dataset.warehouse;
            document.getElementById("assign-hour").value = zone.dataset.hour ?? "8";
            const dateInput = document.getElementById("assign-date");
            if (dateInput) dateInput.value = zone.dataset.date || dateInput.value;
            form.submit();
        });
    });
});
