(function () {
    function getErrorMessages(errors) {
        return (errors || []).map(error => error.message);
    }

    function clearFormErrors(form, generalErrorContainer) {
        form.querySelectorAll(".errorlist").forEach(errorList => {
            errorList.replaceChildren();
            errorList.classList.add("d-none");
        });

        if (generalErrorContainer) {
            generalErrorContainer.replaceChildren();
            generalErrorContainer.classList.add("d-none");
        }
    }

    function renderErrorList(errorList, errors) {
        const messages = getErrorMessages(errors);
        errorList.replaceChildren();
        messages.forEach(message => {
            const item = document.createElement("li");
            item.textContent = message;
            errorList.appendChild(item);
        });
        errorList.classList.toggle("d-none", messages.length === 0);
    }

    function renderFormErrors(form, errors, generalErrorContainer) {
        const generalMessages = [];

        form.querySelectorAll("[data-field-errors]").forEach(errorList => {
            const fieldName = errorList.dataset.fieldErrors;
            const fieldMessages = errors?.[fieldName] || [];
            renderErrorList(errorList, fieldMessages);
        });

        Object.entries(errors || {}).forEach(([fieldName, messages]) => {
            if (!form.querySelector(`[data-field-errors="${fieldName}"]`)) {
                generalMessages.push(...getErrorMessages(messages));
            }
        });

        if (generalErrorContainer) {
            generalErrorContainer.textContent = generalMessages.join(" ");
            generalErrorContainer.classList.toggle("d-none", generalMessages.length === 0);
        }
    }

    function submitJsonForm(form) {
        return fetch(form.action, {
            method: form.method || "POST",
            body: new FormData(form),
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        }).then(response => response.json().then(data => ({ ok: response.ok, data })));
    }

    window.IkanForms = {
        clearFormErrors,
        renderFormErrors,
        submitJsonForm,
    };
}());
