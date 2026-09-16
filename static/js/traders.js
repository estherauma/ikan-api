document.addEventListener('DOMContentLoaded', function () {
  const modalElement = document.getElementById('attach-vessel-owners-modal');
  const attachVesselOwnersForm = document.getElementById(
    'attach-vessel-owners-form',
  );
  const removeVesselOwnerModalElement = document.getElementById(
    'remove-vessel-owner-modal',
  );
  const removeVesselOwnerButtons = document.querySelectorAll(
    '[data-remove-vessel-owner-button]',
  );
  const removeVesselOwnerConfirmButton =
    removeVesselOwnerModalElement?.querySelector(
      '[data-confirmation-modal-confirm]',
    );
  const removeVesselOwnerMessage = removeVesselOwnerModalElement?.querySelector(
    '[data-confirmation-modal-message]',
  );
  const removeVesselOwnerErrors = removeVesselOwnerModalElement?.querySelector(
    '[data-confirmation-modal-errors]',
  );
  const attachVesselOwnersLoader = document.querySelector(
    '[data-fullscreen-loader]',
  );
  const loaderText = attachVesselOwnersLoader?.querySelector(
    '.fullscreen-loader-text',
  );

  if (!modalElement || !attachVesselOwnersForm || !attachVesselOwnersLoader)
    return;
  let removeVesselOwnerUrl = null;
  const removeVesselOwnerDefaultText =
    removeVesselOwnerConfirmButton?.textContent || 'Remove';

  function showLoader(message) {
    if (loaderText) {
      loaderText.textContent = message;
    }
    attachVesselOwnersLoader.classList.remove('d-none');
  }

  function getCsrfToken() {
    return attachVesselOwnersForm.querySelector("[name='csrfmiddlewaretoken']")
      .value;
  }

  function resetAttachVesselOwnersForm() {
    attachVesselOwnersForm.reset();
    const generalErrorContainer = document.getElementById(
      'attach-vessel-owners-errors',
    );
    window.IkanForms.clearFormErrors(
      attachVesselOwnersForm,
      generalErrorContainer,
    );
    attachVesselOwnersForm
      .querySelectorAll('[data-searchable-multi-select-input]')
      .forEach((input) => {
        input.value = '';
        input.dispatchEvent(new Event('input', { bubbles: true }));
      });
    attachVesselOwnersForm
      .querySelectorAll('[data-searchable-multi-select-option]')
      .forEach((option) => {
        option.dispatchEvent(new Event('change', { bubbles: true }));
      });
    attachVesselOwnersForm
      .querySelectorAll('[data-searchable-multi-select-dropdown]')
      .forEach((dropdown) => {
        dropdown.classList.remove('show');
      });
  }

  function showAttachVesselOwnersErrors(errors) {
    const generalErrorContainer = document.getElementById(
      'attach-vessel-owners-errors',
    );
    window.IkanForms.renderFormErrors(
      attachVesselOwnersForm,
      errors,
      generalErrorContainer,
    );
  }

  function showRemoveVesselOwnerError(message) {
    if (!removeVesselOwnerErrors) return;

    removeVesselOwnerErrors.textContent = message;
    removeVesselOwnerErrors.classList.remove('d-none');
  }

  function resetRemoveVesselOwnerModal() {
    removeVesselOwnerUrl = null;
    if (removeVesselOwnerErrors) {
      removeVesselOwnerErrors.classList.add('d-none');
      removeVesselOwnerErrors.textContent = '';
    }
    if (removeVesselOwnerConfirmButton) {
      removeVesselOwnerConfirmButton.disabled = false;
      removeVesselOwnerConfirmButton.textContent = removeVesselOwnerDefaultText;
    }
  }

  attachVesselOwnersForm.addEventListener('submit', function (event) {
    event.preventDefault();
    showAttachVesselOwnersErrors({});
    showLoader('Attaching vessel owners...');

    window.IkanForms.submitJsonForm(attachVesselOwnersForm)
      .then(({ ok, data }) => {
        if (!ok || !data.success) {
          showAttachVesselOwnersErrors(data.errors);
          attachVesselOwnersLoader.classList.add('d-none');

          return;
        }

        bootstrap.Modal.getOrCreateInstance(modalElement).hide();
        window.location.reload();
      })
      .catch(() => {
        showAttachVesselOwnersErrors({
          error: ['Something went wrong. Please try again.'],
        });
        attachVesselOwnersLoader.classList.add('d-none');
      });
  });

  window.addEventListener('pageshow', function () {
    hideLoader();
  });

  modalElement.addEventListener('hidden.bs.modal', function () {
    resetAttachVesselOwnersForm();
  });

  removeVesselOwnerModalElement?.addEventListener(
    'hidden.bs.modal',
    function () {
      resetRemoveVesselOwnerModal();
    },
  );

  removeVesselOwnerButtons.forEach((button) => {
    button.addEventListener('click', function () {
      removeVesselOwnerUrl = button.dataset.removeUrl;
      const vesselOwnerName =
        button.dataset.vesselOwnerName.trim() || 'this vessel owner';

      if (removeVesselOwnerMessage) {
        removeVesselOwnerMessage.textContent = `You are removing ${vesselOwnerName} from the trader. You can attach them again later.`;
      }
      if (removeVesselOwnerErrors) {
        removeVesselOwnerErrors.classList.add('d-none');
        removeVesselOwnerErrors.textContent = '';
      }
      if (removeVesselOwnerConfirmButton) {
        removeVesselOwnerConfirmButton.disabled = false;
        removeVesselOwnerConfirmButton.textContent =
          removeVesselOwnerDefaultText;
      }

      bootstrap.Modal.getOrCreateInstance(removeVesselOwnerModalElement).show();
    });
  });

  removeVesselOwnerConfirmButton?.addEventListener('click', function () {
    if (!removeVesselOwnerUrl) return;

    showLoader('Removing vessel owner...');
    removeVesselOwnerConfirmButton.disabled = true;
    removeVesselOwnerConfirmButton.textContent = 'Removing...';

    fetch(removeVesselOwnerUrl, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrfToken(),
        'X-Requested-With': 'XMLHttpRequest',
      },
    })
      .then((response) =>
        response
          .json()
          .catch(() => ({}))
          .then((data) => ({ ok: response.ok, data })),
      )
      .then(({ ok, data }) => {
        if (!ok || !data.success) {
          showRemoveVesselOwnerError(data.error);
          removeVesselOwnerConfirmButton.disabled = false;
          removeVesselOwnerConfirmButton.textContent =
            removeVesselOwnerDefaultText;
          hideLoader();
          return;
        }

        bootstrap.Modal.getOrCreateInstance(
          removeVesselOwnerModalElement,
        ).hide();
        window.location.reload();
      })
      .catch(() => {
        showRemoveVesselOwnerError('Something went wrong. Please try again.');
        removeVesselOwnerConfirmButton.disabled = false;
        removeVesselOwnerConfirmButton.textContent =
          removeVesselOwnerDefaultText;
        hideLoader();
      });
  });
});
