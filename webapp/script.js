/**
 * Mini App Script for Data Entry Bot
 * Handles data loading, editing, and submission
 */

// Get data from URL parameters
function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const dataParam = params.get('data');
    
    if (dataParam) {
        try {
            return JSON.parse(decodeURIComponent(dataParam));
        } catch (e) {
            console.error('Error parsing data parameter:', e);
            return null;
        }
    }
    
    return null;
}

// Initialize app
function init() {
    const data = getUrlParams();
    
    if (!data) {
        showError('No se encontraron datos para mostrar.');
        return;
    }
    
    // Show loading
    document.getElementById('loading').classList.add('active');
    
    // Simulate loading delay (remove in production)
    setTimeout(() => {
        loadData(data);
    }, 500);
}

// Load data into form
function loadData(data) {
    try {
        // Hide loading
        document.getElementById('loading').classList.remove('active');
        
        // Determine document type
        const tipoDocumento = data.tipo_documento || 'documento';
        document.getElementById('documentType').textContent = 
            tipoDocumento === 'cheque' ? 'Cheque' : 'Documento';
        
        if (tipoDocumento === 'cheque') {
            loadChequeData(data);
        } else {
            loadDocumentData(data);
        }
        
        // Show form
        document.getElementById('formContainer').style.display = 'block';
        
    } catch (e) {
        console.error('Error loading data:', e);
        showError('Error al cargar los datos.');
    }
}

// Load cheque data
function loadChequeData(data) {
    // Show cheque form
    document.getElementById('chequeForm').style.display = 'block';
    document.getElementById('documentForm').style.display = 'none';
    
    // Populate fields
    document.getElementById('cuitLibrador').value = data.cuit_librador || '';
    document.getElementById('banco').value = data.banco || '';
    document.getElementById('fechaEmision').value = data.fecha_emision || '';
    document.getElementById('fechaPago').value = data.fecha_pago || '';
    document.getElementById('importe').value = data.importe || 0;
    document.getElementById('numeroCheque').value = data.numero_cheque || '';
    document.getElementById('cbuBeneficiario').value = data.cbu_beneficiario || '';
    
    // BCRA info (read-only display)
    document.getElementById('estadoBcra').textContent = data.estado_bcra || 'N/A';
    document.getElementById('chequesRechazados').textContent = data.cheques_rechazados || 0;
    document.getElementById('riesgoCrediticio').textContent = data.riesgo_crediticio || 'N/A';
    
    // Add status badge styling
    const estadoBcraEl = document.getElementById('estadoBcra');
    const estado = data.estado_bcra || '';
    
    if (estado.includes('Sin deuda')) {
        estadoBcraEl.className = 'info-value status-badge status-success';
    } else if (estado.includes('moderada')) {
        estadoBcraEl.className = 'info-value status-badge status-warning';
    } else if (estado.includes('alta') || estado.includes('Error')) {
        estadoBcraEl.className = 'info-value status-badge status-danger';
    }
}

// Load general document data
function loadDocumentData(data) {
    // Show document form
    document.getElementById('chequeForm').style.display = 'none';
    document.getElementById('documentForm').style.display = 'block';
    
    // Populate fields
    document.getElementById('contenido').value = data.contenido || '';
    document.getElementById('tipoDocumento').value = data.tipo_documento || 'documento';
}

// Collect form data
function collectFormData() {
    const tipoDocumento = document.getElementById('documentType').textContent.toLowerCase();
    
    if (tipoDocumento === 'cheque') {
        return {
            tipo_documento: 'cheque',
            cuit_librador: document.getElementById('cuitLibrador').value,
            banco: document.getElementById('banco').value,
            fecha_emision: document.getElementById('fechaEmision').value,
            fecha_pago: document.getElementById('fechaPago').value,
            importe: parseFloat(document.getElementById('importe').value) || 0,
            numero_cheque: document.getElementById('numeroCheque').value,
            cbu_beneficiario: document.getElementById('cbuBeneficiario').value || null,
            estado_bcra: document.getElementById('estadoBcra').textContent,
            cheques_rechazados: parseInt(document.getElementById('chequesRechazados').textContent) || 0,
            riesgo_crediticio: document.getElementById('riesgoCrediticio').textContent
        };
    } else {
        return {
            tipo_documento: document.getElementById('tipoDocumento').value || 'documento',
            contenido: document.getElementById('contenido').value,
            datos_estructurados: {},
            metadata: {}
        };
    }
}

// Validate form
function validateForm() {
    const tipoDocumento = document.getElementById('documentType').textContent.toLowerCase();
    
    if (tipoDocumento === 'cheque') {
        const cuit = document.getElementById('cuitLibrador').value;
        const banco = document.getElementById('banco').value;
        const importe = document.getElementById('importe').value;
        
        if (!cuit || !banco || !importe || parseFloat(importe) <= 0) {
            showError('Por favor completa todos los campos obligatorios (CUIT, Banco, Importe).');
            return false;
        }
        
        // Basic CUIT validation
        const cuitRegex = /^\d{2}-\d{8}-\d{1}$/;
        if (!cuitRegex.test(cuit)) {
            showError('El CUIT debe tener el formato XX-XXXXXXXX-X');
            return false;
        }
    }
    
    return true;
}

// Confirm and submit
async function confirm() {
    if (!validateForm()) {
        return;
    }
    
    const confirmBtn = document.getElementById('confirmBtn');
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Procesando...';
    
    try {
        const formData = collectFormData();
        
        // Get user ID from Telegram WebApp if available
        const userId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || null;
        
        const payload = {
            tipo_documento: formData.tipo_documento,
            datos: formData,
            usuario_id: userId ? String(userId) : null,
            timestamp: new Date().toISOString()
        };
        
        // Send to backend
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            const result = await response.json();
            showSuccess('Datos procesados correctamente. ✅');
            
            // Close Mini App after 2 seconds
            setTimeout(() => {
                if (window.Telegram?.WebApp) {
                    window.Telegram.WebApp.close();
                } else {
                    alert('Datos procesados. Puedes cerrar esta ventana.');
                }
            }, 2000);
        } else {
            const error = await response.json();
            showError('Error al procesar los datos: ' + (error.detail || 'Error desconocido'));
            confirmBtn.disabled = false;
            confirmBtn.textContent = 'Confirmar';
        }
        
    } catch (error) {
        console.error('Error submitting data:', error);
        showError('Error de conexión. Por favor intenta nuevamente.');
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Confirmar';
    }
}

// Cancel
function cancel() {
    if (window.Telegram?.WebApp) {
        window.Telegram.WebApp.close();
    } else {
        if (confirm('¿Estás seguro de que quieres cancelar?')) {
            window.close();
        }
    }
}

// Show error message
function showError(message) {
    const alert = document.getElementById('alert');
    alert.textContent = message;
    alert.className = 'alert alert-error active';
    
    setTimeout(() => {
        alert.classList.remove('active');
    }, 5000);
}

// Show success message
function showSuccess(message) {
    const alert = document.getElementById('alert');
    alert.textContent = message;
    alert.className = 'alert alert-success active';
}

// Initialize Telegram WebApp
if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.ready();
    window.Telegram.WebApp.expand();
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}


