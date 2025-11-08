(function(){
  const el = document.getElementById('ordersByDayChart');
  if (!el || !window.DASHBOARD_DATA) return;
  const { labels, values } = window.DASHBOARD_DATA;

  // Create chart
  new Chart(el, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Orders',
        data: values,
        borderColor: 'rgba(54, 162, 235, 1)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        tension: 0.2,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { title: { display: true, text: 'Date' } },
        y: { title: { display: true, text: 'Orders' }, beginAtZero: true, precision: 0 }
      }
    }
  });
})();
