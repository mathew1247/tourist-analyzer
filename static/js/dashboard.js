/**
 * XploreElite Dashboard - Interactive Controller
 * Real Database Destinations with Full Dynamic Modal & Tab Filtering
 */

// Data definitions for the 5 Real Regional Destinations from the Database
const DESTINATION_DETAILS = {
  ooty: {
    key: 'ooty',
    title: 'Ooty (Udhagamandalam)',
    location: 'Nilgiris District, Tamil Nadu, India',
    category: 'Hill Stations',
    days: '3-5 Days',
    rating: '4.8 / 5.0 (520 reviews)',
    visitors: '8,420 registered visitors',
    rawVisitors: 8420,
    revenue: '₹ 18,50,000 gross revenue',
    rawRevenue: 1850000,
    yield: '₹ 2,197 / visitor',
    peak: 'April - June (Summer Festival)',
    image: '../static/images/ooty.jpg',
    description: 'Renowned "Queen of Hill Stations" in the Nilgiri hills. Highlights include Pykara Lake, Doddabetta Peak, and tea plantation estates recorded in state databases.'
  },
  munnar: {
    key: 'munnar',
    title: 'Munnar Tea Sanctuary',
    location: 'Idukki District, Kerala, India',
    category: 'Hill Stations',
    days: '3-4 Days',
    rating: '4.9 / 5.0 (640 reviews)',
    visitors: '14,400 registered visitors',
    rawVisitors: 14400,
    revenue: '₹ 43,20,000 gross revenue',
    rawRevenue: 4320000,
    yield: '₹ 3,000 / visitor',
    peak: 'September - March (Winter Bloom)',
    image: '../static/images/munnar.jpg',
    description: 'Spectacular Western Ghats destination nestled among tea terraced hills, Eravikulam National Park, and Mattupetty Dam. One of the highest revenue-generating destinations in active records.'
  },
  kodaikanal: {
    key: 'kodaikanal',
    title: 'Kodaikanal Mist & Lake',
    location: 'Dindigul District, Tamil Nadu, India',
    category: 'Hill Stations',
    days: '2-3 Days',
    rating: '4.6 / 5.0 (390 reviews)',
    visitors: '5,760 registered visitors',
    rawVisitors: 5760,
    revenue: '₹ 12,80,000 gross revenue',
    rawRevenue: 1280000,
    yield: '₹ 2,222 / visitor',
    peak: 'April - June & Sept - Oct',
    image: '../static/images/kodaikanal.jpg',
    description: 'Renowned lakeside hill haven in the Palani Hills, featuring scenic pine forests, Coakers Walk, Pillar Rocks, and consistent family holiday footfall.'
  },
  coorg: {
    key: 'coorg',
    title: 'Coorg (Kodagu Valley)',
    location: 'Kodagu District, Karnataka, India',
    category: 'Hill Stations',
    days: '2-4 Days',
    rating: '4.7 / 5.0 (410 reviews)',
    visitors: '6,980 registered visitors',
    rawVisitors: 6980,
    revenue: '₹ 15,40,000 gross revenue',
    rawRevenue: 1540000,
    yield: '₹ 2,206 / visitor',
    peak: 'October - March (Coffee Harvest)',
    image: '../static/images/coorg.jpg',
    description: 'Acclaimed "Scotland of India" renowned for lush coffee plantations, Abbey and Iruppu waterfalls, and high weekend tourist influx from major urban hubs.'
  },
  rameswaram: {
    key: 'rameswaram',
    title: 'Rameswaram Island & Temple',
    location: 'Ramanathapuram District, Tamil Nadu, India',
    category: 'Cultural & Heritage',
    days: '2-3 Days',
    rating: '4.8 / 5.0 (480 reviews)',
    visitors: '3,210 registered visitors',
    rawVisitors: 3210,
    revenue: '₹ 9,60,000 gross revenue',
    rawRevenue: 960000,
    yield: '₹ 2,990 / visitor',
    peak: 'July - February (Pilgrim Season)',
    image: '../static/images/rameswaram.jpg',
    description: 'Sacred coastal island sanctuary famed for the historic Ramanathaswamy Temple with monumental sculpted corridors, sacred water theerthams, and scenic Pamban sea bridge.'
  }
};

document.addEventListener('DOMContentLoaded', async () => {
  setupNavigationAndButtons();
  setupSearchHandler();
  setupHotelsSection();
  setupModalDismissals();
  await loadLiveMetrics();
});

/**
 * 1. Fetch live metrics from database and update metric cards & destination badges
 */
async function loadLiveMetrics() {
  try {
    const dashboardData = await TourismAPI.getDashboardData(2025);
    if (dashboardData && dashboardData.summary) {
      // 4 Signature Metric Cards
      const visitorsEl = document.getElementById('dashTotalVisitors');
      if (visitorsEl && dashboardData.summary.total_visitors) {
        visitorsEl.textContent = formatNumber(dashboardData.summary.total_visitors);
      }

      const revenueEl = document.getElementById('dashTotalRevenue');
      if (revenueEl && dashboardData.summary.total_revenue) {
        revenueEl.textContent = formatCurrency(dashboardData.summary.total_revenue);
      }

      const avgVisitorsEl = document.getElementById('dashAvgVisitors');
      if (avgVisitorsEl && dashboardData.summary.avg_visitors) {
        avgVisitorsEl.textContent = formatNumber(dashboardData.summary.avg_visitors);
      }

      const avgRevenueEl = document.getElementById('dashAvgRevenue');
      if (avgRevenueEl && dashboardData.summary.avg_revenue) {
        avgRevenueEl.textContent = formatCurrency(dashboardData.summary.avg_revenue);
      }
    }

    // Sync destination live counts if returned by backend API
    if (dashboardData && Array.isArray(dashboardData.destinations)) {
      dashboardData.destinations.forEach(dest => {
        const key = (dest.name || '').toLowerCase();
        if (DESTINATION_DETAILS[key] && dest.visitors) {
          DESTINATION_DETAILS[key].rawVisitors = dest.visitors;
          DESTINATION_DETAILS[key].visitors = `${formatNumber(dest.visitors)} registered visitors`;
          const badgeEl = document.getElementById(`cardVis-${key}`);
          if (badgeEl) {
            badgeEl.textContent = `${formatNumber(dest.visitors)} visitors`;
          }
        }
      });
    }
  } catch (e) {
    console.log('Using default dashboard metrics', e);
  }

  // Update greeting with real logged-in user if available
  const authUser = sessionStorage.getItem('auth_user');
  if (authUser) {
    const namePart = authUser.split('@')[0];
    const capitalized = namePart.charAt(0).toUpperCase() + namePart.slice(1);
    const greetingEl = document.getElementById('dashboardGreeting');
    if (greetingEl) {
      greetingEl.innerHTML = `Executive Tourism Dashboard <span class="greeting-icon">👋</span>`;
    }
    const headerUserName = document.querySelector('.user-profile-menu .user-name');
    if (headerUserName) {
      headerUserName.textContent = capitalized;
    }
  }
}

/**
 * 2. Setup Navigation & Global Event Handlers
 */
function setupNavigationAndButtons() {
  // Logout triggers
  const logoutButtons = document.querySelectorAll('.logout-trigger, .nav-logout');
  logoutButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      if (confirm('Are you sure you want to log out of XploreElite?')) {
        TourismAPI.logout();
      }
    });
  });
}

/**
 * 3. Search Bar Handler
 */
function setupSearchHandler() {
  const searchInput = document.getElementById('globalSearch');
  const executeSearch = () => {
    const query = (searchInput?.value || '').trim();
    if (query) {
      showToast(`Filtering records for "${query}"...`, 'info');
      setTimeout(() => {
        window.location.href = `records.html?search=${encodeURIComponent(query)}`;
      }, 400);
    } else {
      window.location.href = 'records.html';
    }
  };

  if (searchInput) {
    searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        executeSearch();
      }
    });
  }
}

/**
 * 4. Hotel & Destination Cards, Tab Switching & Modal Open
 */
function setupHotelsSection() {
  // Segmented Pill Tabs
  const tabs = document.querySelectorAll('.tv-tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const tabType = tab.dataset.tab;
      filterHotelsByTab(tabType);
    });
  });

  // Hotel Card Click Listeners -> Opens Dynamic Database Popup Card
  document.querySelectorAll('.tv-hotel-card').forEach(card => {
    card.addEventListener('click', () => {
      const destKey = card.dataset.dest || 'ooty';
      openDestinationModal(destKey);
    });
  });
}

/**
 * Filter destinations grid based on active tab
 */
function filterHotelsByTab(tabType) {
  const cards = Array.from(document.querySelectorAll('.tv-hotel-card'));
  const container = document.querySelector('.tv-cards-grid');

  if (tabType === 'top') {
    // Sort cards by visitor count descending
    cards.sort((a, b) => {
      const visA = parseInt(a.dataset.visitors || '0', 10);
      const visB = parseInt(b.dataset.visitors || '0', 10);
      return visB - visA;
    });
    cards.forEach(card => {
      card.style.display = 'block';
      container.appendChild(card);
    });
    showToast('Sorted destinations by highest visitor footfall', 'info');
    return;
  }

  // Filter by category or all
  cards.forEach((card, index) => {
    const category = card.dataset.category;
    if (tabType === 'all' || category === tabType) {
      card.style.display = 'block';
      card.style.opacity = '0';
      card.style.transform = 'scale(0.95)';
      setTimeout(() => {
        card.style.opacity = '1';
        card.style.transform = 'scale(1)';
        card.style.transition = 'all 0.25s ease';
      }, 50 + index * 40);
    } else {
      card.style.display = 'none';
    }
  });

  if (tabType !== 'all') {
    showToast(`Showing ${tabType} destinations`, 'info');
  }
}

/**
 * 5. Destination Details Popup Modal matching the exact Database UI
 */
function openDestinationModal(destKey) {
  const details = DESTINATION_DETAILS[destKey] || DESTINATION_DETAILS.ooty;
  const modal = document.getElementById('destinationModal');
  if (!modal) return;

  // Populate dynamic database metrics
  document.getElementById('modalDestImg').src = details.image;
  document.getElementById('modalDestImg').alt = details.title;
  document.getElementById('modalDestCategory').textContent = details.category;
  document.getElementById('modalDestTitle').textContent = details.title;
  document.getElementById('modalDestLocation').innerHTML = `
    <i class="fa-solid fa-location-dot" style="color: var(--primary);"></i>
    <span>${details.location}</span>
  `;
  document.getElementById('modalDestDesc').textContent = details.description;
  document.getElementById('modalDestVisitors').textContent = details.visitors;
  document.getElementById('modalDestRevenue').textContent = details.revenue;
  document.getElementById('modalDestYield').textContent = details.yield;
  document.getElementById('modalDestPeak').textContent = details.peak;

  // Action Buttons
  const viewRecBtn = document.getElementById('modalViewRecordsBtn');
  if (viewRecBtn) {
    const searchWord = details.title.split(' ')[0].replace(/[^a-zA-Z]/g, '');
    viewRecBtn.onclick = () => {
      window.location.href = `records.html?search=${encodeURIComponent(searchWord)}`;
    };
  }

  const addDataBtn = document.getElementById('modalAddDataBtn');
  if (addDataBtn) {
    addDataBtn.onclick = () => {
      window.location.href = 'add-data.html';
    };
  }

  modal.classList.add('show');
}

function closeDestinationModal() {
  const modal = document.getElementById('destinationModal');
  if (modal) {
    modal.classList.remove('show');
  }
}

/**
 * 6. Modal Dismissal Events (Backdrop click and Escape key)
 */
function setupModalDismissals() {
  const modal = document.getElementById('destinationModal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeDestinationModal();
      }
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeDestinationModal();
    }
  });
}
