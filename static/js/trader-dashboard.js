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

document.addEventListener('DOMContentLoaded', initSupplierToggles);
