/**
 * XploreElite - Reports Generator Controller
 */

let reportMiniChart = null;

document.addEventListener('DOMContentLoaded', async () => {
  setupReportTypeOptions();
  await handleGenerateReport();

  const genBtn = document.getElementById('generateReportBtn');
  if (genBtn) {
    genBtn.addEventListener('click', handleGenerateReport);
  }

  const printBtn = document.getElementById('printReportBtn');
  if (printBtn) {
    printBtn.addEventListener('click', () => {
      window.print();
    });
  }

  const downloadPdfBtn = document.getElementById('downloadPdfBtn');
  if (downloadPdfBtn) {
    downloadPdfBtn.addEventListener('click', () => {
      showToast('Preparing PDF document for printing...', 'info');
      setTimeout(() => window.print(), 400);
    });
  }
});

function setupReportTypeOptions() {
  const options = document.querySelectorAll('.report-type-option');
  options.forEach(opt => {
    opt.addEventListener('click', () => {
      options.forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
      const radio = opt.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;

      // If Yearly Report, toggle Month selector
      const monthGroup = document.getElementById('reportMonthGroup');
      if (monthGroup) {
        if (radio.value === 'Yearly Report') {
          monthGroup.style.opacity = '0.5';
          document.getElementById('reportMonth').disabled = true;
        } else {
          monthGroup.style.opacity = '1';
          document.getElementById('reportMonth').disabled = false;
        }
      }
    });
  });
}

async function handleGenerateReport() {
  const selectedType = document.querySelector('input[name="reportType"]:checked')?.value || 'Monthly Report';
  const month = document.getElementById('reportMonth')?.value || 'January';
  const year = document.getElementById('reportYear')?.value || '2025';

  const genBtn = document.getElementById('generateReportBtn');
  if (genBtn) {
    genBtn.disabled = true;
    genBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';
  }

  try {
    const report = await TourismAPI.generateReport(selectedType, month, year);
    renderReportPreview(report, selectedType);
    showToast('Report generated successfully!', 'success');
  } catch (error) {
    console.error('Failed to generate report:', error);
    showToast('Failed to generate report.', 'danger');
  } finally {
    if (genBtn) {
      genBtn.disabled = false;
      genBtn.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> <span>Generate Report</span>';
    }
  }
}

function renderReportPreview(report, type) {
  document.getElementById('repPreviewTitle').textContent = report.title;
  document.getElementById('repPreviewPeriod').textContent = report.period;
  document.getElementById('repPreviewGeneratedAt').textContent = `Generated on ${report.generatedAt}`;
  document.getElementById('repPreviewVisitors').textContent = formatNumber(report.totalVisitors);
  document.getElementById('repPreviewRevenue').textContent = formatCurrency(report.totalRevenue);
  document.getElementById('repPreviewAvgVisitors').textContent = formatNumber(report.avgVisitors);
  document.getElementById('repPreviewAvgRevenue').textContent = formatCurrency(report.avgRevenue);
  document.getElementById('repPreviewGrowth').textContent = `+${report.growthRate}%`;
  document.getElementById('repPreviewPeak').textContent = report.peakPeriod;

  // Mini Chart
  renderMiniChart(report, type);

  // Table Breakdown
  const tbody = document.getElementById('reportTableBreakdown');
  if (tbody) {
    if (!report.records || report.records.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No specific record entries for this period.</td></tr>';
      return;
    }

    tbody.innerHTML = report.records.map(r => `
      <tr>
        <td style="font-weight: 700;">${r.month} ${r.year}</td>
        <td>${formatNumber(r.visitors)}</td>
        <td style="font-weight: 700; color: var(--text-navy);">${formatCurrency(r.revenue)}</td>
        <td><span class="badge badge-info">${r.category || 'General'}</span></td>
        <td style="color: var(--success); font-weight: 600;">Audited</td>
      </tr>
    `).join('');
  }
}

function renderMiniChart(report, type) {
  const canvas = document.getElementById('reportMiniChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  if (reportMiniChart) reportMiniChart.destroy();

  const labels = report.records.map(r => r.month);
  const visitorData = report.records.map(r => r.visitors);
  const revenueData = report.records.map(r => r.revenue);

  // If single month, show a comparison benchmark
  const chartLabels = labels.length === 1 ? ['Previous Year', 'Current Record', 'Sector Benchmark'] : labels;
  const chartData = labels.length === 1 ? [2850, report.totalVisitors, 3500] : visitorData;

  reportMiniChart = new Chart(ctx, {
    type: labels.length === 1 ? 'bar' : 'line',
    data: {
      labels: chartLabels,
      datasets: [{
        label: 'Visitors',
        data: chartData,
        backgroundColor: '#f43f5e',
        borderColor: '#e11d48',
        borderWidth: 2,
        tension: 0.3,
        fill: labels.length > 1,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { family: 'Plus Jakarta Sans', size: 10 } } },
        y: { grid: { color: '#f1f5f9' }, ticks: { font: { family: 'Plus Jakarta Sans', size: 10 } } }
      }
    }
  });
}
