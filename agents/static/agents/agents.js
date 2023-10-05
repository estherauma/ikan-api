$(document).ready(function () {
  let columns = [
    { data: 'name', title: 'Name' },
    { data: 'contact_name', title: 'Contact Name' },
    { data: 'email', title: 'Email' },
    { data: 'telephone', title: 'Telephone' },
    { data: 'status', title: 'Status' },
  ];
  $('#agents-table').DataTable({
      ajax: '/agents/data',
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
