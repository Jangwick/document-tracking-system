document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const preview = document.getElementById(`${this.id}-preview`);
            if (preview) {
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                    };
                    reader.readAsDataURL(this.files[0]);
                }
            }
        });
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Search functionality in tables
    const tableSearchInputs = document.querySelectorAll('.table-search');
    tableSearchInputs.forEach(input => {
        input.addEventListener('keyup', function() {
            const tableId = this.getAttribute('data-table-target');
            const table = document.getElementById(tableId);
            
            if (table) {
                const term = this.value.toLowerCase();
                const rows = table.querySelectorAll('tbody tr');
                
                rows.forEach(row => {
                    const textContent = row.textContent.toLowerCase();
                    row.style.display = textContent.includes(term) ? '' : 'none';
                });
            }
        });
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });

    // Confirm delete actions
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Application status chart if Chart.js is available and canvas exists
    const statusChartEl = document.getElementById('applicationStatusChart');
    if (typeof Chart !== 'undefined' && statusChartEl) {
        const ctx = statusChartEl.getContext('2d');
        
        // Get data attributes
        const pending = parseInt(statusChartEl.getAttribute('data-pending') || 0);
        const review = parseInt(statusChartEl.getAttribute('data-review') || 0);
        const approved = parseInt(statusChartEl.getAttribute('data-approved') || 0);
        const rejected = parseInt(statusChartEl.getAttribute('data-rejected') || 0);
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Pending', 'Under Review', 'Approved', 'Rejected'],
                datasets: [{
                    data: [pending, review, approved, rejected],
                    backgroundColor: ['#ffc107', '#0dcaf0', '#198754', '#dc3545'],
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Handle payment form submissions
    const paymentForms = document.querySelectorAll('form[id^="paymentForm"]');
    
    paymentForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Disable the submit button to prevent multiple submissions
            const submitBtn = this.querySelector('.payment-submit-btn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            }
        });
    });

    // Initialize export buttons
    initializeExportButtons();
});

// Function to show/hide password
function togglePasswordVisibility(inputId, iconId) {
    const passwordInput = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Function to initialize all export buttons
function initializeExportButtons() {
    // Applications page exports
    const exportCSV = document.getElementById('exportCSV');
    const exportPDF = document.getElementById('exportPDF');
    const exportPrint = document.getElementById('exportPrint');
    
    // Reports page exports
    const exportCSVBtn = document.getElementById('exportCSVBtn');
    const exportExcelBtn = document.getElementById('exportExcelBtn');
    
    if (exportCSV) {
        exportCSV.addEventListener('click', function(e) {
            e.preventDefault();
            exportTableToCSV('applicationsTable', 'applications.csv');
        });
    }
    
    if (exportPDF) {
        exportPDF.addEventListener('click', function(e) {
            e.preventDefault();
            exportTableToPDF('applicationsTable', 'applications.pdf');
        });
    }
    
    if (exportPrint) {
        exportPrint.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    }
    
    if (exportCSVBtn) {
        exportCSVBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const reportTitle = document.querySelector('h1.fw-bold').innerText || 'System Reports';
            exportReportToCSV(reportTitle.replace(' ', '_').toLowerCase() + '.csv');
        });
    }
    
    if (exportExcelBtn) {
        exportExcelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const reportTitle = document.querySelector('h1.fw-bold').innerText || 'System Reports';
            exportReportToExcel(reportTitle.replace(' ', '_').toLowerCase() + '.xlsx');
        });
    }
}

// Function to export table data to CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Extract headers
    const headers = [];
    const headerCells = table.querySelectorAll('thead th');
    headerCells.forEach(cell => {
        if (!cell.querySelector('.form-check')) { // Skip checkbox column
            headers.push('"' + (cell.innerText.trim() || '') + '"');
        }
    });
    csvContent += headers.join(',') + '\r\n';
    
    // Extract rows
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        if (row.style.display !== 'none') { // Only visible rows
            const rowData = [];
            const cells = row.querySelectorAll('td');
            cells.forEach((cell, index) => {
                if (index > 0) { // Skip checkbox column
                    let cellText = cell.innerText.trim() || '';
                    // Remove any commas or quotes that would break CSV format
                    cellText = cellText.replace(/"/g, '""');
                    rowData.push('"' + cellText + '"');
                }
            });
            csvContent += rowData.join(',') + '\r\n';
        }
    });
    
    // Create download link
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Function to export table data to PDF
function exportTableToPDF(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    // Load jsPDF dynamically
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
    script.onload = function() {
        const scriptAutoTable = document.createElement('script');
        scriptAutoTable.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.23/jspdf.plugin.autotable.min.js';
        scriptAutoTable.onload = function() {
            generatePDF();
        };
        document.body.appendChild(scriptAutoTable);
    };
    document.body.appendChild(script);
    
    function generatePDF() {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        
        // Add title
        doc.setFontSize(18);
        doc.text('Applications Report', 14, 22);
        doc.setFontSize(11);
        doc.setTextColor(100);
        
        // Get table headers and data for AutoTable
        const headers = [];
        const headerCells = table.querySelectorAll('thead th');
        headerCells.forEach(cell => {
            if (!cell.querySelector('.form-check')) { // Skip checkbox column
                headers.push(cell.innerText.trim() || '');
            }
        });
        
        const data = [];
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            if (row.style.display !== 'none') { // Only visible rows
                const rowData = [];
                const cells = row.querySelectorAll('td');
                cells.forEach((cell, index) => {
                    if (index > 0) { // Skip checkbox column
                        rowData.push(cell.innerText.trim() || '');
                    }
                });
                data.push(rowData);
            }
        });
        
        // Generate table
        doc.autoTable({
            head: [headers],
            body: data,
            startY: 30,
            theme: 'striped',
            styles: { fontSize: 10 }
        });
        
        // Save PDF
        doc.save(filename);
    }
}

// Function to export report data to CSV
function exportReportToCSV(filename) {
    // Get data from all visible tables in reports page
    const tables = document.querySelectorAll('.table:not([style*="display: none"])');
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Add report title
    const title = document.querySelector('h1.fw-bold').innerText || 'System Reports';
    csvContent += '"' + title + '"\r\n\r\n';
    
    // Process each table
    tables.forEach(table => {
        // Add section title
        const sectionTitle = table.closest('.card').querySelector('.card-header h5')?.innerText || '';
        if (sectionTitle) {
            csvContent += '"' + sectionTitle + '"\r\n';
        }
        
        // Extract headers
        const headers = [];
        const headerCells = table.querySelectorAll('thead th');
        headerCells.forEach(cell => {
            headers.push('"' + (cell.innerText.trim() || '') + '"');
        });
        csvContent += headers.join(',') + '\r\n';
        
        // Extract rows
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const rowData = [];
            const cells = row.querySelectorAll('td');
            cells.forEach(cell => {
                let cellText = cell.innerText.trim() || '';
                cellText = cellText.replace(/"/g, '""');
                rowData.push('"' + cellText + '"');
            });
            csvContent += rowData.join(',') + '\r\n';
        });
        
        csvContent += '\r\n'; // Add space between tables
    });
    
    // Create download link
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Function to export report data to Excel (XLSX)
function exportReportToExcel(filename) {
    // Load SheetJS library dynamically
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js';
    script.onload = function() {
        generateExcel();
    };
    document.body.appendChild(script);
    
    function generateExcel() {
        const XLSX = window.XLSX;
        const workbook = XLSX.utils.book_new();
        
        // Process each table
        const tables = document.querySelectorAll('.table:not([style*="display: none"])');
        tables.forEach((table, tableIndex) => {
            const sectionTitle = table.closest('.card').querySelector('.card-header h5')?.innerText || 'Sheet' + (tableIndex + 1);
            const sheetName = sectionTitle.substring(0, 31).replace(/[*?:/\\[\]]/g, '_'); // Excel sheet name limitations
            
            // Extract headers
            const headers = [];
            const headerCells = table.querySelectorAll('thead th');
            headerCells.forEach(cell => {
                headers.push(cell.innerText.trim() || '');
            });
            
            // Extract data
            const data = [headers];
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const rowData = [];
                const cells = row.querySelectorAll('td');
                cells.forEach(cell => {
                    rowData.push(cell.innerText.trim() || '');
                });
                data.push(rowData);
            });
            
            const worksheet = XLSX.utils.aoa_to_sheet(data);
            XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
        });
        
        // Generate an overview sheet with charts data
        const chartData = extractChartData();
        if (Object.keys(chartData).length > 0) {
            const overviewData = [['Report Overview']];
            
            Object.entries(chartData).forEach(([title, data]) => {
                overviewData.push([]);
                overviewData.push([title]);
                
                if (Array.isArray(data.labels) && Array.isArray(data.values)) {
                    // Add headers
                    overviewData.push(['Category', 'Value']);
                    
                    // Add data rows
                    data.labels.forEach((label, index) => {
                        overviewData.push([label, data.values[index] || 0]);
                    });
                    
                    overviewData.push([]); // Add empty row between sets
                }
            });
            
            const overviewSheet = XLSX.utils.aoa_to_sheet(overviewData);
            XLSX.utils.book_append_sheet(workbook, overviewSheet, 'Overview');
        }
        
        // Save Excel file
        XLSX.writeFile(workbook, filename);
    }
    
    function extractChartData() {
        const chartData = {};
        const charts = document.querySelectorAll('canvas');
        
        charts.forEach(chart => {
            const title = chart.closest('.card')?.querySelector('.card-header h5')?.innerText || 
                         chart.closest('.card')?.querySelector('.card-title')?.innerText || 
                         'Chart';
                         
            const chartId = chart.id;
            if (chartId && window.Chart && window.Chart.instances) {
                const chartInstance = Object.values(window.Chart.instances)
                    .find(instance => instance.canvas.id === chartId);
                
                if (chartInstance && chartInstance.data && chartInstance.data.datasets) {
                    chartData[title] = {
                        labels: chartInstance.data.labels || [],
                        values: chartInstance.data.datasets[0]?.data || []
                    };
                }
            }
        });
        
        return chartData;
    }
}
