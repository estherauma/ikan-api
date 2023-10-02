$(document).ready(function () {
  let columns = [
    { data: 'name', title: 'Name' },
    { data: 'reg_no', title: 'Registration Num' },
    { data: 'vessel_type', title: 'Type' },
    { data: 'capacity', title: 'Capacity' },
    { data: 'commissioning_date', title: 'Commission Date' },
    { data: 'status', title: 'Status' },
  ];
  $('#vessels-table').DataTable({
      ajax: '/vessels/data',
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
