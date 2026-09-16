document.addEventListener("DOMContentLoaded", function () {
    const modalElement = document.getElementById("attach-vessel-owners-modal");
    const attachVesselOwnersForm = document.getElementById("attach-vessel-owners-form");
    const attachVesselOwnersLoader = document.querySelector("[data-fullscreen-loader]");

    if (!modalElement || !attachVesselOwnersForm || !attachVesselOwnersLoader) return;

    function resetAttachVesselOwnersForm() {
        attachVesselOwnersForm.reset();
        const generalErrorContainer = document.getElementById("attach-vessel-owners-errors");
        window.IkanForms.clearFormErrors(attachVesselOwnersForm, generalErrorContainer);
        attachVesselOwnersForm.querySelectorAll("[data-searchable-multi-select-input]").forEach(input => {
            input.value = "";
            input.dispatchEvent(new Event("input", { bubbles: true }));
        });
        attachVesselOwnersForm.querySelectorAll("[data-searchable-multi-select-option]").forEach(option => {
            option.dispatchEvent(new Event("change", { bubbles: true }));
        });
        attachVesselOwnersForm.querySelectorAll("[data-searchable-multi-select-dropdown]").forEach(dropdown => {
            dropdown.classList.remove("show");
        });
    }

    function showAttachVesselOwnersErrors(errors) {
        const generalErrorContainer = document.getElementById("attach-vessel-owners-errors");
        window.IkanForms.renderFormErrors(attachVesselOwnersForm, errors, generalErrorContainer);
    }

    attachVesselOwnersForm.addEventListener("submit", function (event) {
        event.preventDefault();
        showAttachVesselOwnersErrors({});
        attachVesselOwnersLoader.classList.remove("d-none");

        window.IkanForms.submitJsonForm(attachVesselOwnersForm)
            .then(({ ok, data }) => {
                if (!ok || !data.success) {
                    showAttachVesselOwnersErrors(data.errors);
                    attachVesselOwnersLoader.classList.add("d-none");
                    return;
                }

                bootstrap.Modal.getOrCreateInstance(modalElement).hide();
                window.location.reload();
            })
            .catch(() => {
                showAttachVesselOwnersErrors({ error: ["Something went wrong. Please try again."] });
                attachVesselOwnersLoader.classList.add("d-none");
            });
    });

    window.addEventListener("pageshow", function () {
        attachVesselOwnersLoader.classList.add("d-none");
    });

    modalElement.addEventListener("hidden.bs.modal", function () {
        resetAttachVesselOwnersForm();
    });
});
