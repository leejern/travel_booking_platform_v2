let bookingsChart, usersChart, paymentStatusChart, roomTypesChart;

// Initialize all charts
function initializeCharts() {
    initializeBookingsChart();
    initializeUsersChart();
    initializePaymentStatusChart();
    initializeRoomTypesChart();
}

// Initialize Bookings Chart
function initializeBookingsChart() {
    const bookingsCtx = document.getElementById('bookingsChart').getContext('2d');
    bookingsChart = new Chart(bookingsCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Bookings',
                data: [],
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Revenue ($)',
                data: [],
                borderColor: '#198754',
                backgroundColor: 'rgba(25, 135, 84, 0.1)',
                tension: 0.4,
                yAxisID: 'y1',
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Number of Bookings'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Revenue ($)'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// Initialize Users Chart
function initializeUsersChart() {
    const usersCtx = document.getElementById('usersChart').getContext('2d');
    usersChart = new Chart(usersCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'New Users',
                data: [],
                backgroundColor: 'rgba(111, 66, 193, 0.8)',
                borderColor: '#6f42c1',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Users'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        }
    });
}

// Initialize Payment Status Chart
function initializePaymentStatusChart() {
    const paymentCtx = document.getElementById('paymentStatusChart').getContext('2d');
    paymentStatusChart = new Chart(paymentCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#198754', // Paid - Green
                    '#ffc107', // Pending - Yellow
                    '#dc3545', // Cancelled - Red
                    '#6c757d', // Failed - Gray
                    '#0d6efd'  // Processing - Blue
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Initialize Room Types Chart (Fixed for Chart.js 3.x)
function initializeRoomTypesChart() {
    const roomTypesCtx = document.getElementById('roomTypesChart').getContext('2d');
    roomTypesChart = new Chart(roomTypesCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Bookings',
                data: [],
                backgroundColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56',
                    '#4BC0C0',
                    '#9966FF',
                    '#FF9F40'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y', // This makes it horizontal
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Bookings'
                    }
                }
            }
        }
    });
}

// Load all reports data
async function loadAllReports() {
    try {
        showLoadingState();
        
        // Load statistics
        await loadStatistics();
        
        // Load charts data
        await loadChartsData();
        
        // Load tables data
        await loadTopHotels();
        await loadRecentBookings();
        
        // Update last updated timestamp
        updateTimestamp();
        
    } catch (error) {
        console.error('Error loading reports:', error);
        showErrorMessage('Failed to load reports data. Please try again.');
    }
}

// Show loading state
function showLoadingState() {
    const statNumbers = document.querySelectorAll('.stat-number');
    statNumbers.forEach(el => el.textContent = 'Loading...');
    
    const summaryValues = document.querySelectorAll('.summary-card .value');
    summaryValues.forEach(el => el.textContent = 'Loading...');
}

// Load statistics data
async function loadStatistics() {
    try {
        const dateRange = document.getElementById('dateRange').value;
        const hotelFilter = document.getElementById('hotelFilter').value;
        
        const response = await fetch(`/admin/reports/statistics/?days=${dateRange}&hotel=${hotelFilter}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch statistics');
        }
        
        const data = await response.json();
        
        // Update main statistics
        document.getElementById('totalBookings').textContent = formatNumber(data.total_bookings);
        document.getElementById('totalRevenue').textContent = formatCurrency(data.total_revenue);
        document.getElementById('totalUsers').textContent = formatNumber(data.total_users);
        document.getElementById('activeHotels').textContent = formatNumber(data.active_hotels);
        
        // Update summary statistics
        document.getElementById('avgBookingValue').textContent = formatCurrency(data.avg_booking_value);
        document.getElementById('userRetention').textContent = formatPercentage(data.user_retention);
        document.getElementById('availableRooms').textContent = formatNumber(data.available_rooms);
        document.getElementById('featuredHotels').textContent = formatNumber(data.featured_hotels);
        
    } catch (error) {
        console.error('Error loading statistics:', error);
        showErrorMessage('Failed to load statistics');
    }
}

// Load charts data
async function loadChartsData() {
    try {
        const dateRange = document.getElementById('dateRange').value;
        const hotelFilter = document.getElementById('hotelFilter').value;
        
        // Load bookings and revenue data
        const bookingsResponse = await fetch(`/admin/reports/bookings-chart/?days=${dateRange}&hotel=${hotelFilter}`);
        const bookingsData = await bookingsResponse.json();
        
        // Update bookings chart
        bookingsChart.data.labels = bookingsData.labels;
        bookingsChart.data.datasets[0].data = bookingsData.bookings;
        bookingsChart.data.datasets[1].data = bookingsData.revenue;
        bookingsChart.update();
        
        // Load users data
        const usersResponse = await fetch(`/admin/reports/users-chart/?days=${dateRange}`);
        const usersData = await usersResponse.json();
        
        // Update users chart
        usersChart.data.labels = usersData.labels;
        usersChart.data.datasets[0].data = usersData.users;
        usersChart.update();
        
        // Load payment status data
        const paymentResponse = await fetch(`/admin/reports/payment-status/?days=${dateRange}&hotel=${hotelFilter}`);
        const paymentData = await paymentResponse.json();
        
        // Update payment status chart
        paymentStatusChart.data.labels = paymentData.labels;
        paymentStatusChart.data.datasets[0].data = paymentData.data;
        paymentStatusChart.update();
        
        // Load room types data
        const roomTypesResponse = await fetch(`/admin/reports/room-types/?days=${dateRange}&hotel=${hotelFilter}`);
        const roomTypesData = await roomTypesResponse.json();
        
        // Update room types chart
        roomTypesChart.data.labels = roomTypesData.labels;
        roomTypesChart.data.datasets[0].data = roomTypesData.data;
        roomTypesChart.update();
        
    } catch (error) {
        console.error('Error loading charts data:', error);
    }
}

// Load top hotels data
async function loadTopHotels() {
    try {
        const dateRange = document.getElementById('dateRange').value;
        
        const response = await fetch(`/admin/reports/top-hotels/?days=${dateRange}`);
        const data = await response.json();
        
        const tbody = document.getElementById('topHotelsBody');
        tbody.innerHTML = '';
        
        data.hotels.forEach(hotel => {
            console.log(`Hotel: ${hotel.name}, Bookings: ${hotel.bookings}, Revenue: ${hotel.revenue}, Rooms: ${hotel.total_rooms}, Views: ${hotel.views}, Featured: ${hotel.is_featured}`);
            console.log("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++");
            console.log(hotel);
            
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${hotel.name}</strong></td>
                <td>${formatNumber(hotel.bookings)}</td>
                <td>${formatCurrency(hotel.revenue)}</td>
                <td>${formatNumber(hotel.total_rooms)}</td>
                <td>${formatNumber(hotel.views)}</td>
                <td>${hotel.is_featured ? '<span class="status-badge status-paid">Yes</span>' : '<span class="status-badge status-cancelled">No</span>'}</td>
            `;
            tbody.appendChild(row);
        });
        
        // Show table and hide loading
        document.getElementById('topHotelsLoading').style.display = 'none';
        document.getElementById('topHotelsTable').style.display = 'table';
        
    } catch (error) {
        console.error('Error loading top hotels:', error);
        document.getElementById('topHotelsLoading').innerHTML = '<i class="fas fa-exclamation-triangle"></i> Failed to load hotels data';
    }
}

// Load recent bookings data
async function loadRecentBookings() {
    try {
        const response = await fetch('/admin/reports/recent-bookings/');
        const data = await response.json();
        
        const tbody = document.getElementById('recentBookingsBody');
        tbody.innerHTML = '';
        
        data.bookings.forEach(booking => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>#${booking.id}</strong></td>
                <td>${booking.guest_name}</td>
                <td>${booking.hotel_name}</td>
                <td>${formatCurrency(booking.amount)}</td>
                <td>${getStatusBadge(booking.status)}</td>
                <td>${formatDate(booking.created_at)}</td>
            `;
            tbody.appendChild(row);
        });
        
        // Show table and hide loading
        document.getElementById('recentBookingsLoading').style.display = 'none';
        document.getElementById('recentBookingsTable').style.display = 'table';
        
    } catch (error) {
        console.error('Error loading recent bookings:', error);
        document.getElementById('recentBookingsLoading').innerHTML = '<i class="fas fa-exclamation-triangle"></i> Failed to load bookings data';
    }
}

// Utility functions
function formatNumber(num) {
    return new Intl.NumberFormat().format(num || 0);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'KSH'
    }).format(amount || 0);
}

function formatPercentage(value) {
    return `${(value || 0).toFixed(1)}%`;
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getStatusBadge(status) {
    const statusMap = {
        'paid': 'status-paid',
        'pending': 'status-pending',
        'cancelled': 'status-cancelled',
        'processing': 'status-processing'
    };
    
    const statusClass = statusMap[status.toLowerCase()] || 'status-cancelled';
    return `<span class="status-badge ${statusClass}">${status}</span>`;
}

function updateTimestamp() {
    const now = new Date();
    document.getElementById('lastUpdated').textContent = now.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showErrorMessage(message) {
    console.error(message);
    alert(message);
}

// Export functions
function exportToPDF() {
    window.open('/admin/reports/export/pdf/', '_blank');
}

function exportToExcel() {
    window.open('/admin/reports/export/excel/', '_blank');
}

function exportToCSV() {
    window.open('/admin/reports/export/csv/', '_blank');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    loadAllReports();
    
    // Add event listeners for filters
    document.getElementById('dateRange').addEventListener('change', loadAllReports);
    document.getElementById('hotelFilter').addEventListener('change', loadAllReports);
});