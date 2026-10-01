/**
 * XploreElite - Tourism Simple Trend Prediction Controller
 * Note: Uses historical moving averages and seasonal linear growth rates.
 */

let predVisitorChart = null;
let predRevenueChart = null;
let currentPeriod = 'next_month';

document.addEventListener('DOMContentLoaded', async () => {
  await loadPrediction(currentPeriod);
  setupPeriodTabs();
});

async function loadPrediction(period) {
  try {
    const data = await TourismAPI.getPrediction(period);
    renderPredictionCards(data);
    renderVisitorForecastChart(data);
    renderRevenueForecastChart(data);
    renderForecastTable(data);
  } catch (error) {
    console.error('Failed to load predictions:', error);
    showToast('Failed to load prediction estimates.', 'danger');
  }
}

function renderPredictionCards(data) {
  document.getElementById('predVisitorsVal').textContent = `${formatNumber(data.predictedVisitors)} visitors`;
  document.getElementById('predRevenueVal').textContent = formatCurrency(data.predictedRevenue);
  document.getElementById('predVisitorGrowthVal').textContent = `+${data.visitorGrowth}%`;
  document.getElementById('predRevenueGrowthVal').textContent = `+${data.revenueGrowth}%`;

  const periodBadge = document.getElementById('activePeriodBadge');
  if (periodBadge) periodBadge.textContent = data.periodLabel;
}

function renderVisitorForecastChart(data) {
  const ctx = document.getElementById('predVisitorChart').getContext('2d');
  
  // Combine labels: Historical + Forecast
  const allLabels = [...data.historical.labels, ...data.forecast.labels];
  
  // Dataset 1: Actual historical visitors (null for forecast slots)
  const actualData = [...data.historical.visitors, ...Array(data.forecast.labels.length).fill(null)];
  
  // Dataset 2: Predicted data connected seamlessly from the last actual point
  const lastActual = data.historical.visitors[data.historical.visitors.length - 1];
  const predictedData = [
    ...Array(data.historical.visitors.length - 1).fill(null),
    lastActual,
    ...data.forecast.visitors
  ];

  if (predVisitorChart) predVisitorChart.destroy();

  predVisitorChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: allLabels,
      datasets: [
        {
          label: 'Actual Data',
          data: actualData,
          borderColor: '#1e293b',
          backgroundColor: 'rgba(30, 41, 59, 0.08)',
          borderWidth: 2.5,
          tension: 0.3,
          fill: false,
          pointBackgroundColor: '#1e293b',
          pointRadius: 4
        },
        {
          label: 'Predicted Data (Linear Model)',
          data: predictedData,
          borderColor: '#e11d48',
          borderDash: [6, 6],
          borderWidth: 2.5,
          tension: 0.3,
          fill: true,
          backgroundColor: 'rgba(225, 29, 72, 0.1)',
          pointBackgroundColor: '#e11d48',
          pointRadius: 5,
          pointHoverRadius: 7
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { font: { family: 'Plus Jakarta Sans', size: 12, weight: 600 } }
        },
        tooltip: {
          backgroundColor: '#0f172a',
          cornerRadius: 8,
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${formatNumber(ctx.raw)} visitors`
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#64748b' } },
        y: {
          grid: { color: '#f1f5f9' },
          ticks: { color: '#64748b', callback: (v) => v >= 1000 ? `${v/1000}K` : v }
        }
      }
    }
  });
}

function renderRevenueForecastChart(data) {
  const ctx = document.getElementById('predRevenueChart').getContext('2d');
  
  const allLabels = [...data.historical.labels, ...data.forecast.labels];
  const actualData = [...data.historical.revenue, ...Array(data.forecast.labels.length).fill(null)];
  const predictedData = [...Array(data.historical.revenue.length).fill(null), ...data.forecast.revenue];

  if (predRevenueChart) predRevenueChart.destroy();

  predRevenueChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: allLabels,
      datasets: [
        {
          label: 'Actual Revenue',
          data: actualData,
          backgroundColor: '#475569',
          borderRadius: 4,
          maxBarThickness: 20
        },
        {
          label: 'Predicted Revenue',
          data: predictedData,
          backgroundColor: '#f43f5e',
          borderRadius: 4,
          maxBarThickness: 20
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { font: { family: 'Plus Jakarta Sans', size: 12, weight: 600 } }
        },
        tooltip: {
          backgroundColor: '#0f172a',
          cornerRadius: 8,
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#64748b' } },
        y: {
          grid: { color: '#f1f5f9' },
          ticks: { color: '#64748b', callback: (v) => v >= 100000 ? `${v/100000}L` : v }
        }
      }
    }
  });
}

function renderForecastTable(data) {
  const tbody = document.getElementById('forecastTableBody');
  if (!tbody) return;

  tbody.innerHTML = data.forecast.labels.map((month, idx) => {
    const v = data.forecast.visitors[idx];
    const r = data.forecast.revenue[idx];
    const avg = Math.round(r / v);
    return `
      <tr>
        <td style="font-weight: 700; color: var(--text-navy);">${month}</td>
        <td style="font-weight: 700; color: var(--primary);">${formatNumber(v)} visitors</td>
        <td style="font-weight: 700; color: var(--text-navy);">${formatCurrency(r)}</td>
        <td>${formatCurrency(avg)}</td>
        <td><span class="badge badge-success">+15% expected</span></td>
        <td><span class="badge badge-primary">Historical Moving Avg</span></td>
      </tr>
    `;
  }).join('');
}

function setupPeriodTabs() {
  const tabs = document.querySelectorAll('.prediction-tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', async () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentPeriod = tab.dataset.period;
      showToast(`Recalculating trend forecast for ${tab.textContent}...`, 'info');
      await loadPrediction(currentPeriod);
    });
  });
}
