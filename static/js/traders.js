function getFullscreenLoader() {
  return document.querySelector('[data-fullscreen-loader]');
}

function showFullscreenLoader() {
  const loader = getFullscreenLoader();

  if (!loader) return;

  loader.classList.remove('d-none');
}

function hideFullscreenLoader() {
  getFullscreenLoader()?.classList.add('d-none');
}

function getCsrfToken() {
  return document.querySelector("[name='csrfmiddlewaretoken']")?.value || '';
}

function initAttachVesselOwners() {
  const modalElement = document.getElementById('attach-vessel-owners-modal');
  const attachVesselOwnersForm = document.getElementById(
    'attach-vessel-owners-form',
  );

  if (!modalElement || !attachVesselOwnersForm || !getFullscreenLoader())
    return;

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

  attachVesselOwnersForm.addEventListener('submit', function (event) {
    event.preventDefault();
    showAttachVesselOwnersErrors({});
    showFullscreenLoader();

    window.IkanForms.submitJsonForm(attachVesselOwnersForm)
      .then(({ ok, data }) => {
        if (!ok || !data.success) {
          showAttachVesselOwnersErrors(data.errors);
          hideFullscreenLoader();

          return;
        }

        bootstrap.Modal.getOrCreateInstance(modalElement).hide();
        window.location.reload();
      })
      .catch(() => {
        showAttachVesselOwnersErrors({
          error: ['Something went wrong. Please try again.'],
        });
        hideFullscreenLoader();
      });
  });

  window.addEventListener('pageshow', function () {
    hideFullscreenLoader();
  });

  modalElement.addEventListener('hidden.bs.modal', function () {
    resetAttachVesselOwnersForm();
  });
}

function initRemoveVesselOwners() {
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

  if (!removeVesselOwnerModalElement || !removeVesselOwnerConfirmButton) return;

  let removeVesselOwnerUrl = null;
  const removeVesselOwnerDefaultText =
    removeVesselOwnerConfirmButton.textContent || 'Remove';

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
    removeVesselOwnerConfirmButton.disabled = false;
    removeVesselOwnerConfirmButton.textContent = removeVesselOwnerDefaultText;
  }

  removeVesselOwnerModalElement.addEventListener(
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
      removeVesselOwnerConfirmButton.disabled = false;
      removeVesselOwnerConfirmButton.textContent =
        removeVesselOwnerDefaultText;

      bootstrap.Modal.getOrCreateInstance(removeVesselOwnerModalElement).show();
    });
  });

  removeVesselOwnerConfirmButton.addEventListener('click', function () {
    if (!removeVesselOwnerUrl) return;

    showFullscreenLoader();
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
          hideFullscreenLoader();
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
        hideFullscreenLoader();
      });
  });
}

function initResendTraderInvites() {
  const resendInviteForms = document.querySelectorAll(
    '[data-resend-invite-form]',
  );

  resendInviteForms.forEach((form) => {
    const submitButton = form.querySelector(
      'button[type="submit"], input[type="submit"]',
    );
    const messageContainer = form.querySelector(
      '[data-resend-invite-message]',
    );
    const modalElement = form.closest('.modal');
    const defaultButtonText = submitButton?.textContent || 'Resend invite';

    function showResendInviteMessage(message, isSuccess) {
      if (!messageContainer) return;

      messageContainer.textContent = message;
      messageContainer.classList.remove(
        'd-none',
        'alert-success',
        'alert-danger',
      );
      messageContainer.classList.add(
        isSuccess ? 'alert-success' : 'alert-danger',
      );
    }

    function resetSubmitButton() {
      if (!submitButton) return;

      submitButton.disabled = false;
      submitButton.textContent = defaultButtonText;
    }

    form.addEventListener('submit', function (event) {
      event.preventDefault();

      if (messageContainer) {
        messageContainer.classList.add('d-none');
        messageContainer.textContent = '';
      }
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Resending...';
      }

      showFullscreenLoader();

      window.IkanForms.submitJsonForm(form)
        .then(({ ok, data }) => {
          if (ok && data.success && modalElement) {
            bootstrap.Modal.getOrCreateInstance(modalElement).hide();
          }

          showResendInviteMessage(
            data.message,
            ok && data.success,
          );
        })
        .catch(() => {
          showResendInviteMessage(
            'Something went wrong. Please try again.',
            false,
          );
        })
        .finally(() => {
          hideFullscreenLoader();
          resetSubmitButton();
        });
    });

    window.addEventListener('pageshow', function () {
      hideFullscreenLoader();
      resetSubmitButton();
    });
  });
}

function initInviteTrader() {
  const inviteTraderForm = document.querySelector('[data-invite-trader-form]');
  const inviteTraderModalElement = document.getElementById(
    'invite-trader-modal',
  );
  const inviteTraderErrors = document.getElementById('invite-trader-errors');

  if (!inviteTraderForm || !inviteTraderModalElement) return;

  const submitButton = inviteTraderForm.querySelector(
    'button[type="submit"], input[type="submit"]',
  );
  const defaultButtonText = submitButton?.textContent || 'Add Trader';

  function resetSubmitButton() {
    if (!submitButton) return;

    submitButton.disabled = false;
    submitButton.textContent = defaultButtonText;
  }

  function clearInviteTraderErrors() {
    window.IkanForms.clearFormErrors(inviteTraderForm, inviteTraderErrors);
  }

  function showInviteTraderErrors(errors, message) {
    window.IkanForms.renderFormErrors(
      inviteTraderForm,
      errors,
      inviteTraderErrors,
    );

    if (
      message &&
      inviteTraderErrors &&
      inviteTraderErrors.classList.contains('d-none')
    ) {
      inviteTraderErrors.textContent = message;
      inviteTraderErrors.classList.remove('d-none');
    }
  }

  inviteTraderForm.addEventListener('submit', function (event) {
    event.preventDefault();

    clearInviteTraderErrors();
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = 'Adding...';
    }
    showFullscreenLoader();

    window.IkanForms.submitJsonForm(inviteTraderForm)
      .then(({ ok, data }) => {
        if (!ok || !data.success) {
          showInviteTraderErrors(data.errors || {}, data.message);
          hideFullscreenLoader();
          resetSubmitButton();
          return;
        }

        bootstrap.Modal.getOrCreateInstance(inviteTraderModalElement).hide();
        window.location.reload();
      })
      .catch(() => {
        showInviteTraderErrors(
          {},
          'Something went wrong. Please try again.',
        );
        hideFullscreenLoader();
        resetSubmitButton();
      });
  });

  inviteTraderModalElement.addEventListener('hidden.bs.modal', function () {
    inviteTraderForm.reset();
    clearInviteTraderErrors();
    resetSubmitButton();
  });

  window.addEventListener('pageshow', function () {
    hideFullscreenLoader();
    resetSubmitButton();
  });
}

document.addEventListener('DOMContentLoaded', function () {
  initAttachVesselOwners();
  initRemoveVesselOwners();
  initResendTraderInvites();
  initInviteTrader();
});
