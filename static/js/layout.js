(function () {
  const sidebar = document.querySelector("[data-sidebar]");
  const toggle = document.querySelector("[data-sidebar-toggle]");
  const body = document.body;
  const storageKey = "sapSidebarCollapsed";

  if (!sidebar || !toggle || !body) return;

  const applyState = (collapsed) => {
    sidebar.classList.toggle("is-collapsed", collapsed);
    body.classList.toggle("sidebar-collapsed", collapsed);
    toggle.setAttribute("aria-expanded", (!collapsed).toString());
    toggle.setAttribute("aria-label", collapsed ? "사이드바 펼치기" : "사이드바 접기");
  };

  const initialState = localStorage.getItem(storageKey) === "1";
  applyState(initialState);

  toggle.addEventListener("click", () => {
    const collapsed = !sidebar.classList.contains("is-collapsed");
    applyState(collapsed);
    localStorage.setItem(storageKey, collapsed ? "1" : "0");
  });
})();
