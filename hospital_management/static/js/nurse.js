$(document).ready(function() {
    $('.patient-card button').click(function() {
        var patientCard = $(this).closest('.patient-card');

        patientCard.addClass('finished');
    });
});
