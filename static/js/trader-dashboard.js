function initSupplierToggles() {
  document.querySelectorAll('[data-supplier-toggle]').forEach(function (button) {
    button.addEventListener('click', function () {
      const card = button.closest('.supplier-card');

      if (card) {
        card.classList.toggle('is-expanded');
      }
    });
  });
}

function initSupplierStatusFilter() {
  const toggle = document.querySelector('[data-status-filter-toggle]');
  const menu = document.querySelector('[data-status-filter-menu]');

  if (!toggle || !menu) {
    return;
  }

  let selectedStatus = 'all';

  function applyStatusFilter(status) {
    document.querySelectorAll('[data-supplier-status]').forEach(function (card) {
      card.hidden = status !== 'all' && card.dataset.supplierStatus !== status;
    });
    selectedStatus = status;
    updateToggleButton();
  }

  function updateToggleButton() {
    const selectedOption = menu.querySelector('[data-status-filter-option="' + selectedStatus + '"]');
    if (selectedOption) {
      toggle.textContent = selectedOption.textContent;
      const icon = document.createElement('i');
      icon.className = 'mdi mdi-chevron-down';
      toggle.appendChild(icon);
    }
  }

  toggle.addEventListener('click', function () {
    menu.hidden = !menu.hidden;
  });

  menu.querySelectorAll('[data-status-filter-option]').forEach(function (option) {
    option.addEventListener('click', function () {
      applyStatusFilter(option.dataset.statusFilterOption);
      menu.hidden = true;
    });
  });

  document.addEventListener('click', function (event) {
    if (!menu.hidden && !menu.contains(event.target) && !toggle.contains(event.target)) {
      menu.hidden = true;
    }
  });
}

function initTraderDashboard() {
  initSupplierToggles();
  initSupplierStatusFilter();
}

document.addEventListener('DOMContentLoaded', initTraderDashboard);
