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

  const exportAllCheckbox = document.getElementById("export-all-columns");
  const exportResultsBtn = document.getElementById("export-btn");
  if (exportAllCheckbox && exportResultsBtn) {
    const baseExportHref = exportResultsBtn.getAttribute("href") || "";

    const updateExportHref = () => {
      if (!baseExportHref) return;
      const url = new URL(baseExportHref, window.location.origin);
      if (exportAllCheckbox.checked) {
        url.searchParams.set("full_data", "1");
      } else {
        url.searchParams.delete("full_data");
      }
      exportResultsBtn.href = url.pathname + url.search;
    };

    try {
      const currentUrl = new URL(baseExportHref, window.location.origin);
      exportAllCheckbox.checked = currentUrl.searchParams.get("full_data") === "1";
    } catch (error) {
      // Ignore invalid base href; leave checkbox unchecked
    }

    exportAllCheckbox.addEventListener("change", updateExportHref);
    updateExportHref();
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
  const detailCache = new Map();
  const MATERIALS_CHUNK = 80;
  const WORK_CHUNK = 80;
  let materialsMoreBtn = null;
  let workMoreBtn = null;

  const renderLinks = (links = []) => {
    linkList.textContent = "";
    if (!links.length) return;
    const fragment = document.createDocumentFragment();
    links.forEach((href, index) => {
      const link = document.createElement("a");
      link.className = "detail-modal__link";
      link.href = href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = links.length > 1 ? `첨부자료 ${index + 1}` : "첨부자료";
      fragment.appendChild(link);
    });
    linkList.appendChild(fragment);
  };

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
  };

  const ensureModalVisible = () => {
    if (!modal.classList.contains("is-active")) {
      modal.classList.add("is-active");
      modal.setAttribute("aria-hidden", "false");
    }
  };

  const openModal = (data, fallbackDatasetLabel = "") => {
    const longText = (data.long_text || "").trim();
    const links = Array.isArray(data.long_text_links) ? data.long_text_links : [];
    const materials = Array.isArray(data.materials) ? data.materials : [];
    const workDetails = Array.isArray(data.work_details) ? data.work_details : [];

    ensureModalVisible();

    // DOM 업데이트를 다음 프레임으로 밀어 렌더 지연을 줄임
    requestAnimationFrame(() => {
      datasetEl.textContent = data.dataset_label || fallbackDatasetLabel || "";
      titleEl.textContent = data.order_no ? `Order #${data.order_no}` : "상세 정보";

      if (exportBtn) {
        if (data.order_no) {
          exportBtn.style.display = "inline-flex";
          exportBtn.href = `/order/${data.order_no}/export`;
        } else {
          exportBtn.style.display = "none";
          exportBtn.removeAttribute("href");
        }
      }

      if (workSection) {
        if (workDetails.length) {
          workSection.classList.remove("is-hidden");
          workContainer.innerHTML = renderWorkDetails(workDetails.slice(0, WORK_CHUNK));
          if (workMoreBtn) {
            workMoreBtn.remove();
            workMoreBtn = null;
          }
          if (workDetails.length > WORK_CHUNK) {
            workMoreBtn = document.createElement("button");
            workMoreBtn.type = "button";
            workMoreBtn.className = "detail-modal__more-btn";
            workMoreBtn.textContent = `작업 ${workDetails.length - WORK_CHUNK}개 더보기`;
            workMoreBtn.addEventListener("click", () => {
              workContainer.innerHTML = renderWorkDetails(workDetails);
              workMoreBtn.remove();
              workMoreBtn = null;
            });
            workSection.appendChild(workMoreBtn);
          }
        } else {
          workSection.classList.add("is-hidden");
          workContainer.innerHTML = "";
          if (workMoreBtn) {
            workMoreBtn.remove();
            workMoreBtn = null;
          }
        }
      }

      if (longText || links.length) {
        longTextSection.classList.remove("is-hidden");
        longTextContainer.textContent = longText || "";
        renderLinks(links);
      } else {
        longTextSection.classList.add("is-hidden");
        longTextContainer.textContent = "";
        linkList.textContent = "";
      }

      if (materials.length) {
        materialsSection.classList.remove("is-hidden");
        materialsContainer.innerHTML = renderMaterials(materials.slice(0, MATERIALS_CHUNK));
        if (materialsMoreBtn) {
          materialsMoreBtn.remove();
          materialsMoreBtn = null;
        }
        if (materials.length > MATERIALS_CHUNK) {
          materialsMoreBtn = document.createElement("button");
          materialsMoreBtn.type = "button";
          materialsMoreBtn.className = "detail-modal__more-btn";
          materialsMoreBtn.textContent = `자재 ${materials.length - MATERIALS_CHUNK}개 더보기`;
          materialsMoreBtn.addEventListener("click", () => {
            materialsContainer.innerHTML = renderMaterials(materials);
            materialsMoreBtn.remove();
            materialsMoreBtn = null;
          });
          materialsSection.appendChild(materialsMoreBtn);
        }
      } else {
        materialsSection.classList.add("is-hidden");
        materialsContainer.innerHTML = "";
        if (materialsMoreBtn) {
          materialsMoreBtn.remove();
          materialsMoreBtn = null;
        }
      }

      const hasDetails =
        Boolean(longText) || links.length > 0 || materials.length > 0 || workDetails.length > 0;
      emptyState.classList.toggle("is-hidden", hasDetails);
    });
  };

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest(".detail-btn");
    if (!trigger) return;
    const orderNo = trigger.getAttribute("data-order-no");
    if (!orderNo) return;
    event.preventDefault();

    const datasetLabel = trigger.getAttribute("data-dataset") || "";

    if (detailCache.has(orderNo)) {
      openModal(detailCache.get(orderNo), datasetLabel);
      return;
    }

    fetch(`/api/order/${encodeURIComponent(orderNo)}/detail`, { method: "GET" })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to load detail (${response.status})`);
        }
        return response.json();
      })
      .then((data) => {
        detailCache.set(orderNo, data);
        openModal(data, datasetLabel);
      })
      .catch((error) => {
        console.error(error);
        longTextContainer.textContent = "상세 정보를 불러오지 못했습니다.";
        linkList.textContent = "";
        materialsContainer.innerHTML = "";
        workContainer.innerHTML = "";
        emptyState.classList.remove("is-hidden");
      });
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
});
