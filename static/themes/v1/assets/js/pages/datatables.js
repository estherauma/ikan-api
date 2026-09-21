$(document).ready(function () {
    const paginationLanguage = {
        paginate: {
            previous: "<i class='mdi mdi-chevron-left'>",
            next: "<i class='mdi mdi-chevron-right'>"
        }
    };

    function addRoundedPagination() {
        $(".dataTables_paginate > .pagination").addClass("pagination-rounded");
    }

    function initDataTable(selector, options) {
        const table = $(selector);

        if (!table.length) {
            return null;
        }

        return table.DataTable($.extend(true, {
            language: paginationLanguage,
            drawCallback: addRoundedPagination
        }, options || {}));
    }

    function getColumnIndexes(value) {
        if (!value) {
            return [];
        }

        return value.split(",")
            .map(function (columnIndex) {
                return parseInt(columnIndex.trim(), 10);
            })
            .filter(function (columnIndex) {
                return !Number.isNaN(columnIndex);
            });
    }

    const defaultTable = $("#datatable");

    if (defaultTable.length) {
        const pageLength = parseInt(defaultTable.data("page-length"), 10) || 20;
        const hideControls = defaultTable.data("hide-controls") === true;
        const sortableColumns = getColumnIndexes(defaultTable.data("sortable-columns"));
        const columnDefs = sortableColumns.length
            ? [
                { targets: sortableColumns, orderable: true },
                { targets: "_all", orderable: false }
            ]
            : [];

        initDataTable("#datatable", {
            pageLength: pageLength,
            dom: hideControls
                ? "rt<'row mt-2'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>"
                : undefined,
            columnDefs: columnDefs
        });
    }

    initDataTable("#basic-datatable");

    const datatableButtons = initDataTable("#datatable-buttons", {
        lengthChange: false,
        buttons: [
            { extend: "copy", className: "btn-light" },
            { extend: "print", className: "btn-light" },
            { extend: "pdf", className: "btn-light" }
        ]
    });

    initDataTable("#selection-datatable", {
        select: {
            style: "multi"
        }
    });

    initDataTable("#key-datatable", {
        keys: true
    });

    if (datatableButtons) {
        datatableButtons.buttons().container().appendTo("#datatable-buttons_wrapper .col-md-6:eq(0)");
    }

    initDataTable("#alternative-page-datatable", {
        pagingType: "full_numbers"
    });

    initDataTable("#scroll-vertical-datatable", {
        scrollY: "350px",
        scrollCollapse: true,
        paging: false
    });

    initDataTable("#scroll-horizontal-datatable", {
        scrollX: true
    });

    initDataTable("#complex-header-datatable", {
        columnDefs: [
            { visible: false, targets: -1 }
        ]
    });

    initDataTable("#row-callback-datatable", {
        createdRow: function (row, data) {
            if (150000 < +data[5].replace(/[\$,]/g, "")) {
                $("td", row).eq(5).addClass("text-danger");
            }
        }
    });

    initDataTable("#state-saving-datatable", {
        stateSave: true
    });

    $(".dataTables_length select").addClass("form-select form-select-sm");
    $(".dataTables_length select").removeClass("custom-select custom-select-sm");
    $(".dataTables_length label").addClass("form-label");
});
