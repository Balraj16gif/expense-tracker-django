document.addEventListener('DOMContentLoaded', function () {
  var dataEl = document.getElementById('chart-data');
  if (!dataEl || typeof Chart === 'undefined') return;

  var data = JSON.parse(dataEl.textContent);
  Chart.defaults.color = getComputedStyle(document.body).color;

  var colors = ['#0d6efd', '#dc3545', '#198754', '#ffc107', '#6f42c1', '#fd7e14', '#20c997', '#6c757d'];

  // Pie chart: category-wise expense
  var pieCanvas = document.getElementById('categoryChart');
  if (pieCanvas && data.pie_values.length > 0) {
    new Chart(pieCanvas, {
      type: 'pie',
      data: {
        labels: data.pie_labels,
        datasets: [{ data: data.pie_values, backgroundColor: colors }]
      },
      options: {
        plugins: { legend: { position: 'bottom' } }
      }
    });
  }

  // Bar chart: month-wise expense and income
  var barCanvas = document.getElementById('monthlyChart');
  if (barCanvas) {
    new Chart(barCanvas, {
      type: 'bar',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        datasets: [
          { label: 'Expense', data: data.bar_expense, backgroundColor: '#dc3545' },
          { label: 'Income', data: data.bar_income, backgroundColor: '#198754' }
        ]
      },
      options: {
        scales: { y: { beginAtZero: true } },
        plugins: { legend: { position: 'bottom' } }
      }
    });
  }

  // Reload when theme is toggled so chart text colors match
  var toggle = document.getElementById('themeToggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      setTimeout(function () { location.reload(); }, 100);
    });
  }
});