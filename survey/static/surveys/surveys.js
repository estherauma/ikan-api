$(document).ready(function () {
    let columns = [
      { data: 'questionKey', title: 'Question Key' },
      { data: 'questionText', title: 'Question Text' },
      { data: 'questionResponse', title: 'Question Response' },
    ];
    $('#surveys-table').DataTable({
        ajax: '/surveys/data',
        columnDefs: [],
        columns: columns,
        dom: 'Bfrtipl',
        buttons: [
            'excelHtml5',
            'csvHtml5',
            'pdfHtml5'
        ]
    });
  });
  