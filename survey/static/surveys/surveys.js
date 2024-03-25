$(document).ready(function () {
    let columns = [
      { data: 'questionText', title: 'Survey Questions' },
      { data: 'action', title: '' },
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
  