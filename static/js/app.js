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

    const form = document.getElementById("assign-form");
    let draggingId = "";
    let justDragged = false;
    const markOver = (zone) => {
        document.querySelectorAll(".drop-zone.is-over").forEach((item) => {
            if (item !== zone) item.classList.remove("is-over");
        });
        if (zone) zone.classList.add("is-over");
    };
    const clearDrag = () => {
        draggingId = "";
        markOver(null);
    };
    document.querySelectorAll(".ship-card, .slot[data-id]").forEach((card) => {
        card.addEventListener("dragstart", (event) => {
            draggingId = String(card.dataset.id || "");
            justDragged = true;
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", draggingId);
            try {
                event.dataTransfer.setDragImage(card, 24, 24);
            } catch (err) {
                /* ignore */
            }
        });
        card.addEventListener("dragend", clearDrag);
        card.addEventListener("click", (event) => {
            if (justDragged) {
                event.preventDefault();
                justDragged = false;
                return;
            }
            if (card.dataset.href) window.location.href = card.dataset.href;
        });
    });
    const scheduleRoot = document.querySelector(".sched-grid") || document.querySelector(".schedule-layout");
    if (scheduleRoot) {
        scheduleRoot.addEventListener("dragover", (event) => {
            const zone = event.target.closest(".drop-zone");
            if (!zone) return;
            event.preventDefault();
            event.dataTransfer.dropEffect = "move";
            markOver(zone);
        });
        scheduleRoot.addEventListener("drop", (event) => {
            const zone = event.target.closest(".drop-zone");
            if (!zone) return;
            event.preventDefault();
            const shipmentId = draggingId || event.dataTransfer.getData("text/plain");
            markOver(null);
            if (!form || !shipmentId) return;
            document.getElementById("assign-shipment").value = shipmentId;
            document.getElementById("assign-warehouse").value = zone.dataset.warehouse;
            document.getElementById("assign-hour").value = zone.dataset.hour ?? "8";
            const dateInput = document.getElementById("assign-date");
            if (dateInput) dateInput.value = zone.dataset.date || dateInput.value;
            form.submit();
        });
    }
});
