$(document).ready(function () {
    let columns = [
      { data: 'name', title: 'Name' },
      { data: 'country', title: 'Country' },
      { data: 'city', title: 'City' },
      { data: 'status', title: 'Status' },
      { data: 'description', title: 'Description'},
      { data: 'actions', title: 'Actions'}
    ];
    $('#companies-table').DataTable({
        ajax: '/companies/data',
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
  