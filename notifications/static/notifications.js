$(document).ready(function () {
    let columns = [
        { data: 'title', title: 'Title' },
        { data: 'message', title: 'Message' },
        { data: 'status', title: 'Status' },
        { data: 'is_displayed', title: 'Is displayed' },
        { data: 'actions', title: 'Actions'}
    ];
    $('#notifications-table').DataTable({
        ajax: '/notifications/data',
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
