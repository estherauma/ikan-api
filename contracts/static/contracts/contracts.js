$(document).ready(function () {
    let columns = [
        { data: 'name', title: 'Name' },
        { data: 'start_date', title: 'Start Date' },
        { data: 'end_date', title: 'End Date' },
        { data: 'kind', title: 'Kind' },
    ];
    $('#contracts-table').DataTable({
        ajax: '/contracts/data',
        columnDefs: [
            {
                targets: [3],
                orderData: [0, 1],
            },
            {
                targets: [3],
                orderData: [1, 0],
            }
        ],
        columns: columns,
        dom: 'Bfrtipl',
        buttons: [
            'excelHtml5',
            'csvHtml5',
            'pdfHtml5'
        ]
    });
});
