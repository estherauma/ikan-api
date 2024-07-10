$(document).ready(function () {
  function initializeDataTable(selector, dataUrl, columns) {
    $(selector).DataTable({
      ajax: dataUrl,
      columnDefs: [],
      columns: columns,
      dom: "Bfrtipl",
      buttons: ["excelHtml5", "csvHtml5", "pdfHtml5"],
    });
  }

  const surveyColumns = [
    { data: "questionText", title: "Survey Questions" },
    { data: "action", title: "" },
  ];
  const TFAVideoColumns = [
    { data: "questionText", title: "TFA Video Questions" },
    { data: "action", title: "" },
  ];
  const inlineQtnColumns = [
    { data: "questionText", title: "Inline Questions" },
    { data: "action", title: "" },
  ];

  initializeDataTable("#surveys-table", "/surveys/data", surveyColumns);
  initializeDataTable("#tfa-video-qtns-table", "/surveys/tfa-video/data/", TFAVideoColumns);
  initializeDataTable("#inline-questions-table", "/surveys/inline-questions/data/", inlineQtnColumns);
});
