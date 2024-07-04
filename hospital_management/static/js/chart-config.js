// document.addEventListener("DOMContentLoaded", function() {
//     // Get blood pressure data from Django template and format it for the chart
//     var bloodPressureData = [];
//     {% for sorted_vital_signs_id, sorted_vital_signs_data in sorted_vital_signs.items %}
//         bloodPressureData.push({ x: "{{ sorted_vital_signs_data.date }} {{ sorted_vital_signs_data.time }}", y: "{{ sorted_vital_signs_data.bloodpressure }}" });
//     {% endfor %}

//     // Chart configuration
//     var ctx = document.getElementById('bloodPressureChart').getContext('2d');
//     var myChart = new Chart(ctx, {
//         type: 'line',
//         data: {
//             datasets: [{
//                 label: 'Blood Pressure',
//                 data: bloodPressureData,
//                 borderColor: 'rgb(75, 192, 192)',
//                 tension: 0.1
//             }]
//         },
//         options: {
//             scales: {
//                 x: {
//                     type: 'time',
//                     time: {
//                         unit: 'day'
//                     }
//                 },
//                 y: {
//                     title: {
//                         display: true,
//                         text: 'Blood Pressure'
//                     }
//                 }
//             }
//         }
//     });
// });
