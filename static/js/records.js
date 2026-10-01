/**
 * XploreElite - Tourism Records Management
 */

let recordsData = [];
let currentPage = 1;
const pageSize = 8;
let deleteTargetId = null;

document.addEventListener('DOMContentLoaded', async () => {
  // Read URL params (e.g. from global search or dashboard edit button)
  const urlParams = new URLSearchParams(window.location.search);
  const searchParam = urlParams.get('search');
  const editParam = urlParams.get('edit');

  if (searchParam) {
    const searchInput = document.getElementById('recordSearch');
    if (searchInput) searchInput.value = searchParam;
  }

  await loadRecords();
  setupFilterListeners();

  if (editParam) {
    setTimeout(() => {
      openEditModal(editParam);
    }, 300);
  }
});

async function loadRecords() {
  try {
    const filters = getActiveFilters();
    recordsData = await TourismAPI.getRecords(filters);
    renderTable();
  } catch (error) {
    console.error('Error loading records:', error);
    showToast('Failed to load tourism records.', 'danger');
  }
}

function getActiveFilters() {
  return {
    search: document.getElementById('recordSearch')?.value.trim() || '',
    year: document.getElementById('yearFilter')?.value || 'all',
    month: document.getElementById('monthFilter')?.value || 'all',
    category: document.getElementById('categoryFilter')?.value || 'all'
  };
}

function renderTable() {
  const tbody = document.getElementById('recordsTableBody');
  const emptyState = document.getElementById('emptyState');
  const tableWrapper = document.getElementById('tableContentWrapper');
  const countText = document.getElementById('recordsCountText');
  const pagination = document.getElementById('recordsPagination');

  if (!tbody) return;

  const total = recordsData.length;

  if (total === 0) {
    if (tableWrapper) tableWrapper.style.display = 'none';
    if (emptyState) emptyState.style.display = 'block';
    if (countText) countText.textContent = 'Showing 0 records';
    if (pagination) pagination.innerHTML = '';
    return;
  }

  if (tableWrapper) tableWrapper.style.display = 'block';
  if (emptyState) emptyState.style.display = 'none';

  // Calculate pagination slice
  const totalPages = Math.ceil(total / pageSize);
  if (currentPage > totalPages) currentPage = totalPages || 1;
  const startIdx = (currentPage - 1) * pageSize;
  const endIdx = Math.min(startIdx + pageSize, total);

  if (countText) {
    countText.textContent = `Showing ${startIdx + 1}–${endIdx} of ${total} records`;
  }

  const pageRecords = recordsData.slice(startIdx, endIdx);

  tbody.innerHTML = pageRecords.map(r => `
    <tr data-id="${r.id}">
      <td style="font-weight: 700; color: var(--text-navy);">${r.month}</td>
      <td style="font-weight: 600;">${r.year}</td>
      <td>
        <span style="font-weight: 700; color: var(--text-navy);">${formatNumber(r.visitors)}</span>
        <span style="font-size: 0.8rem; color: var(--text-muted); margin-left: 3px;">tourists</span>
      </td>
      <td style="font-weight: 700; color: var(--text-navy);">${formatCurrency(r.revenue)}</td>
      <td>
        <span class="badge ${getCategoryBadgeClass(r.category)}">${r.category || 'General'}</span>
      </td>
      <td style="color: var(--text-muted); font-size: 0.85rem;">${r.created_at || '2025-01-15'}</td>
      <td>
        <div class="action-btn-group">
          <button class="btn-icon view" onclick="openViewModal(${r.id})" title="View Details">
            <i class="fa-regular fa-eye"></i>
          </button>
          <button class="btn-icon edit" onclick="openEditModal(${r.id})" title="Edit Record">
            <i class="fa-regular fa-pen-to-square"></i>
          </button>
          <button class="btn-icon delete" onclick="confirmDeleteRecord(${r.id})" title="Delete Record">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </div>
      </td>
    </tr>
  `).join('');

  renderPagination(totalPages);
}

function getCategoryBadgeClass(cat) {
  switch (cat) {
    case 'Beach Tourism': return 'badge-primary';
    case 'Hill Stations': return 'badge-info';
    case 'Cultural & Heritage': return 'badge-success';
    case 'Adventure': return 'badge-warning';
    default: return 'badge-secondary';
  }
}

function renderPagination(totalPages) {
  const container = document.getElementById('recordsPagination');
  if (!container || totalPages <= 1) {
    if (container) container.innerHTML = '';
    return;
  }

  let html = `
    <button class="page-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="goToPage(${currentPage - 1})">
      <i class="fa-solid fa-chevron-left"></i>
    </button>
  `;

  for (let i = 1; i <= totalPages; i++) {
    html += `
      <button class="page-btn ${currentPage === i ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>
    `;
  }

  html += `
    <button class="page-btn" ${currentPage === totalPages ? 'disabled' : ''} onclick="goToPage(${currentPage + 1})">
      <i class="fa-solid fa-chevron-right"></i>
    </button>
  `;

  container.innerHTML = html;
}

function goToPage(page) {
  currentPage = page;
  renderTable();
}

function setupFilterListeners() {
  const searchInput = document.getElementById('recordSearch');
  const yearFilter = document.getElementById('yearFilter');
  const monthFilter = document.getElementById('monthFilter');
  const categoryFilter = document.getElementById('categoryFilter');
  const resetBtn = document.getElementById('resetFiltersBtn');

  const onFilterChange = async () => {
    currentPage = 1;
    await loadRecords();
  };

  if (searchInput) {
    searchInput.addEventListener('input', debounce(onFilterChange, 250));
  }
  if (yearFilter) yearFilter.addEventListener('change', onFilterChange);
  if (monthFilter) monthFilter.addEventListener('change', onFilterChange);
  if (categoryFilter) categoryFilter.addEventListener('change', onFilterChange);

  if (resetBtn) {
    resetBtn.addEventListener('click', async () => {
      if (searchInput) searchInput.value = '';
      if (yearFilter) yearFilter.value = 'all';
      if (monthFilter) monthFilter.value = 'all';
      if (categoryFilter) categoryFilter.value = 'all';
      currentPage = 1;
      await loadRecords();
    });
  }
}

// View Record Modal
async function openViewModal(id) {
  try {
    const record = await TourismAPI.getRecord(id);
    const avgPerVisitor = Math.round(record.revenue / (record.visitors || 1));

    document.getElementById('viewModalMonthYear').textContent = `${record.month} ${record.year}`;
    document.getElementById('viewModalCategory').textContent = record.category || 'General';
    document.getElementById('viewModalCategory').className = `badge ${getCategoryBadgeClass(record.category)}`;
    document.getElementById('viewModalVisitors').textContent = formatNumber(record.visitors);
    document.getElementById('viewModalRevenue').textContent = formatCurrency(record.revenue);
    document.getElementById('viewModalAvgSpend').textContent = formatCurrency(avgPerVisitor);
    document.getElementById('viewModalCreated').textContent = record.created_at || 'Verified';

    const modal = document.getElementById('viewRecordModal');
    modal.classList.add('show');
  } catch (err) {
    showToast('Record not found.', 'danger');
  }
}

// Edit Record Modal
async function openEditModal(id) {
  try {
    const record = await TourismAPI.getRecord(id);
    document.getElementById('editRecordId').value = record.id;
    document.getElementById('editMonth').value = record.month;
    document.getElementById('editYear').value = record.year;
    document.getElementById('editVisitors').value = record.visitors;
    document.getElementById('editRevenue').value = record.revenue;
    document.getElementById('editCategory').value = record.category || 'Hill Stations';

    // Reset validations
    ['editMonth', 'editYear', 'editVisitors', 'editRevenue'].forEach(fId => {
      document.getElementById(fId)?.classList.remove('is-invalid');
    });

    const modal = document.getElementById('editRecordModal');
    modal.classList.add('show');
  } catch (err) {
    showToast('Could not load record for editing.', 'danger');
  }
}

async function handleEditFormSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('editRecordId').value;
  const month = document.getElementById('editMonth').value;
  const year = document.getElementById('editYear').value;
  const visitors = parseInt(document.getElementById('editVisitors').value, 10);
  const revenue = parseFloat(document.getElementById('editRevenue').value);
  const category = document.getElementById('editCategory').value;

  let isValid = true;
  if (!month) { document.getElementById('editMonth').classList.add('is-invalid'); isValid = false; }
  if (!year) { document.getElementById('editYear').classList.add('is-invalid'); isValid = false; }
  if (isNaN(visitors) || visitors <= 0) { document.getElementById('editVisitors').classList.add('is-invalid'); isValid = false; }
  if (isNaN(revenue) || revenue <= 0) { document.getElementById('editRevenue').classList.add('is-invalid'); isValid = false; }

  if (!isValid) return;

  try {
    await TourismAPI.updateRecord(id, { month, year, visitors, revenue, category });
    closeModals();
    showToast('Record updated successfully!', 'success');
    await loadRecords();
  } catch (err) {
    showToast('Failed to update record.', 'danger');
  }
}

// Delete Record
function confirmDeleteRecord(id) {
  deleteTargetId = id;
  const modal = document.getElementById('deleteConfirmModal');
  modal.classList.add('show');
}

async function executeDelete() {
  if (!deleteTargetId) return;
  try {
    await TourismAPI.deleteRecord(deleteTargetId);
    deleteTargetId = null;
    closeModals();
    showToast('Record deleted successfully.', 'success');
    await loadRecords();
  } catch (err) {
    showToast('Failed to delete record.', 'danger');
  }
}

function closeModals() {
  document.querySelectorAll('.modal-backdrop').forEach(m => m.classList.remove('show'));
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
