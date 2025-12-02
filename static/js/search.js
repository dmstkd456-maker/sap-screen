document.addEventListener("DOMContentLoaded", () => {
  const resetBtn = document.querySelector(".reset-btn");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      window.location = "/";
    });
  }

  const backBtn = document.querySelector(".back-btn");
  if (backBtn) {
    backBtn.addEventListener("click", () => {
      window.history.back();
    });
  }

  const modal = document.getElementById("detail-modal");
  if (!modal) return;

  const datasetEl = document.getElementById("detail-modal-dataset");
  const titleEl = document.getElementById("detail-modal-title");
  const exportBtn = document.getElementById("detail-modal-export-btn");
  const workSection = document.getElementById("detail-modal-work-section");
  const workContainer = document.getElementById("detail-modal-work");
  const longTextSection = document.getElementById("detail-modal-longtext-section");
  const longTextContainer = document.getElementById("detail-modal-longtext");
  const linkList = document.getElementById("detail-modal-link-list");
  const materialsSection = document.getElementById("detail-modal-materials-section");
  const materialsContainer = document.getElementById("detail-modal-materials");
  const emptyState = document.getElementById("detail-modal-empty");
  const closeBtn = modal.querySelector("[data-modal-close]");

  const escapeHtml = (value) => {
    return String(value || "-")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  };

  const renderMaterials = (materials) => {
    const header = "<tr>" + "<th>Material</th>" + "<th>Description</th>" + "<th>Qty</th>" + "<th>UoM</th>" + "</tr>";
    const rows = materials
      .map((item) => {
        return (
          "<tr>" +
          `<td>${escapeHtml(item.material || "") || "-"}</td>` +
          `<td>${escapeHtml(item.description || "") || "-"}</td>` +
          `<td>${escapeHtml(item.qty || "") || "-"}</td>` +
          `<td>${escapeHtml(item.uom || "") || "-"}</td>` +
          "</tr>"
        );
      })
      .join("");
    return '<table class="detail-modal__materials-table">' + header + rows + "</table>";
  };

  const renderWorkDetails = (details) => {
    if (!Array.isArray(details) || !details.length) return "";
    const header =
      "<tr>" +
      "<th>Start of Execution</th>" +
      "<th>작업자 이름</th>" +
      "<th>Actual Work</th>" +
      "<th>Unit</th>" +
      "</tr>";
    const rows = details
      .map((item) => {
        return (
          "<tr>" +
          `<td>${escapeHtml(item.start_of_execution || "") || "-"}</td>` +
          `<td>${escapeHtml(item.worker_name || "") || "-"}</td>` +
          `<td>${escapeHtml(item.actual_work || "") || "-"}</td>` +
          `<td>${escapeHtml(item.work_unit || "") || "-"}</td>` +
          "</tr>"
        );
      })
      .join("");
    return '<table class="detail-modal__work-table">' + header + rows + "</table>";
  };

  const closeModal = () => {
    modal.classList.remove("is-active");
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-open");
  };

  const openModal = (data) => {
    const longText = (data.long_text || "").trim();
    const links = Array.isArray(data.long_text_links) ? data.long_text_links : [];
    const materials = Array.isArray(data.materials) ? data.materials : [];
    const workDetails = Array.isArray(data.work_details) ? data.work_details : [];

    datasetEl.textContent = data.dataset_label || "";
    titleEl.textContent = data.order_no ? `Order #${data.order_no}` : "상세 정보";

    if (exportBtn) {
      if (data.order_no) {
        exportBtn.style.display = "inline-flex";
        exportBtn.href = `/order/${data.order_no}/export_detail`;
      } else {
        exportBtn.style.display = "none";
        exportBtn.removeAttribute("href");
      }
    }

    if (workSection) {
      if (workDetails.length) {
        workSection.classList.remove("is-hidden");
        workContainer.innerHTML = renderWorkDetails(workDetails);
      } else {
        workSection.classList.add("is-hidden");
        workContainer.innerHTML = "";
      }
    }

    if (longText || links.length) {
      longTextSection.classList.remove("is-hidden");
      longTextContainer.innerHTML = longText ? longText.replace(/\n/g, "<br>") : "";
      linkList.innerHTML = "";
    } else {
      longTextSection.classList.add("is-hidden");
      longTextContainer.innerHTML = "";
      linkList.innerHTML = "";
    }

    if (materials.length) {
      materialsSection.classList.remove("is-hidden");
      materialsContainer.innerHTML = renderMaterials(materials);
    } else {
      materialsSection.classList.add("is-hidden");
      materialsContainer.innerHTML = "";
    }

    const hasDetails = Boolean(longText) || links.length > 0 || materials.length > 0 || workDetails.length > 0;
    emptyState.classList.toggle("is-hidden", hasDetails);

    modal.classList.add("is-active");
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
  };

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest(".detail-btn");
    if (!trigger) return;
    const payload = trigger.getAttribute("data-detail");
    if (!payload) return;
    event.preventDefault();
    try {
      const data = JSON.parse(payload);
      openModal(data);
    } catch (error) {
      console.error("Failed to parse detail payload", error);
    }
  });

  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeModal();
    }
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", closeModal);
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && modal.classList.contains("is-active")) {
      closeModal();
    }
  });

  // Handle export checkbox for "모든 정보"
  const exportCheckbox = document.getElementById("export-all-columns");
  const exportButton = document.getElementById("export-btn");

  if (exportCheckbox && exportButton) {
    const baseUrl = exportButton.getAttribute("href");

    exportCheckbox.addEventListener("change", () => {
      if (exportCheckbox.checked) {
        // Add full_data=1 parameter to URL
        const url = new URL(baseUrl, window.location.origin);
        url.searchParams.set("full_data", "1");
        exportButton.setAttribute("href", url.pathname + url.search);
      } else {
        // Reset to original URL
        exportButton.setAttribute("href", baseUrl);
      }
    });
  }
});
