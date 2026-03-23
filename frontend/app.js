// Global variables
let uploadedFiles = {
    saldos: null,
    resgates: null
};

let currentFilter = 'all';
let logs = [];

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupFileUploads();
    setupEventListeners();
    setupLogFilter();
    
    // Add welcome message
    addLogMessage({
        timestamp: new Date().toLocaleString('pt-BR'),
        level: 'INFO',
        color: '#17a2b8',
        message: 'Sistema ETL inicializado. Aguardando arquivos para processamento.',
        details: ''
    });
}

function setupFileUploads() {
    // Setup saldos file upload
    setupFileUpload('saldos');
    setupFileUpload('resgates');
}

function setupFileUpload(type) {
    const uploadArea = document.getElementById(`${type}Upload`);
    const fileInput = document.getElementById(`${type}File`);
    
    // Click to upload
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        handleFileSelect(type, e.target.files[0]);
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(type, files[0]);
        }
    });
}

function handleFileSelect(type, file) {
    if (!file) return;
    
    // Validate file type
    const allowedTypes = ['.csv', '.xlsx', '.xls'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        addLogMessage({
            timestamp: new Date().toLocaleString('pt-BR'),
            level: 'ERROR',
            color: '#dc3545',
            message: `Formato de arquivo não suportado: ${fileExtension}`,
            details: `Formatos aceitos: ${allowedTypes.join(', ')}`
        });
        return;
    }
    
    // Ler o conteúdo do arquivo como Base64
    const reader = new FileReader();
    reader.onload = async function(event) {
        const base64data = event.target.result.split(",")[1]; // Remove o prefixo data:image/png;base64,

        // Chamar a função de upload do backend
        const uploadResult = await eel.upload_file(file.name, base64data)();

        if (uploadResult.success) {
            uploadedFiles[type] = file; // Armazenar o objeto File original
            updateFileInfo(type, file);
            updateProcessButton();

            addLogMessage({
                timestamp: new Date().toLocaleString("pt-BR"),
                level: "SUCCESS",
                color: "#28a745",
                message: `Arquivo de ${type} carregado e enviado: ${file.name}`,
                details: `Tamanho: ${formatFileSize(file.size)}`
            });
        } else {
            addLogMessage({
                timestamp: new Date().toLocaleString("pt-BR"),
                level: "ERROR",
                color: "#dc3545",
                message: `Erro ao enviar arquivo de ${type}: ${file.name}`,
                details: uploadResult.error
            });
        }
    };
    reader.readAsDataURL(file);
}

function updateFileInfo(type, file) {
    const uploadArea = document.getElementById(`${type}Upload`);
    const fileInfo = document.getElementById(`${type}Info`);
    
    // Hide upload area, show file info
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';
    
    // Update file details
    const fileName = fileInfo.querySelector('.file-name');
    const fileSize = fileInfo.querySelector('.file-size');
    
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
}

async function removeFile(type) {
    const fileToRemove = uploadedFiles[type];
    if (!fileToRemove) return;

    // Chamar a função de exclusão do backend
    const deleteResult = await eel.delete_uploaded_file(fileToRemove.name)();

    if (deleteResult.success) {
        uploadedFiles[type] = null;
    
        // Reset UI
        const uploadArea = document.getElementById(`${type}Upload`);
        const fileInfo = document.getElementById(`${type}Info`);
        const fileInput = document.getElementById(`${type}File`);
        
        uploadArea.style.display = 'block';
        fileInfo.style.display = 'none';
        fileInput.value = '';
        
        updateProcessButton();
        
        addLogMessage({
            timestamp: new Date().toLocaleString('pt-BR'),
            level: 'INFO',
            color: '#17a2b8',
            message: `Arquivo de ${type} removido`,
            details: ''
        });
    } else {
            addLogMessage({
                timestamp: new Date().toLocaleString('pt-BR'),
                level: 'ERROR',
                color: '#dc3545',
                message: `Erro ao remover arquivo de ${type}: ${fileToRemove.name}`,
                details: deleteResult.error
            });
        }
}

function updateProcessButton() {
    const processBtn = document.getElementById('processBtn');
    const hasAllFiles = uploadedFiles.saldos && uploadedFiles.resgates;
    
    processBtn.disabled = !hasAllFiles;
    
    if (hasAllFiles) {
        processBtn.innerHTML = '<i class="fas fa-play"></i> Iniciar Processamento ETL';
    } else {
        processBtn.innerHTML = '<i class="fas fa-upload"></i> Selecione os arquivos primeiro';
    }
}

function setupEventListeners() {
    // Process button
    document.getElementById('processBtn').addEventListener('click', startETLProcess);
    
    // Clear logs button
    document.getElementById('clearLogsBtn').addEventListener('click', clearLogs);
    
    // Config button
    document.getElementById('configBtn').addEventListener('click', () => {
        openModal('configModal');
        loadDatabaseConfig();
    });
    
    // Export logs button
    document.getElementById('exportLogsBtn').addEventListener('click', exportLogs);
    
    // Database type change
    document.getElementById('dbType').addEventListener('change', updateDatabaseConfig);
}

function setupLogFilter() {
    const logFilter = document.getElementById('logFilter');
    logFilter.addEventListener('change', (e) => {
        currentFilter = e.target.value;
        filterLogs();
    });
}

async function startETLProcess() {
    if (!uploadedFiles.saldos || !uploadedFiles.resgates) {
        addLogMessage({
            timestamp: new Date().toLocaleString('pt-BR'),
            level: 'ERROR',
            color: '#dc3545',
            message: 'Selecione ambos os arquivos antes de iniciar o processamento',
            details: ''
        });
        return;
    }
    
    // Disable process button
    const processBtn = document.getElementById('processBtn');
    processBtn.disabled = true;
    processBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
    
    // Show progress section
    const progressSection = document.getElementById('progressSection');
    progressSection.style.display = 'block';
    
    try {
        // Clear previous logs
        clearLogs();
        
        addLogMessage({
            timestamp: new Date().toLocaleString('pt-BR'),
            level: 'INFO',
            color: '#17a2b8',
            message: 'Iniciando processamento ETL...',
            details: 'Preparando arquivos para upload'
        });
        
        // Upload files and start processing
        const result = await eel.start_etl_process(
            uploadedFiles.saldos.name,
            uploadedFiles.resgates.name
        )();
        
        if (result.success) {
            updateProgress('Processamento concluído', 100);
            
            addLogMessage({
                timestamp: new Date().toLocaleString('pt-BR'),
                level: 'SUCCESS',
                color: '#28a745',
                message: 'Processamento ETL concluído com sucesso!',
                details: `Banco de dados: ${result.database_path}`
            });
            
            // Show results modal
            showResults(result);
        } else {
            addLogMessage({
                timestamp: new Date().toLocaleString('pt-BR'),
                level: 'ERROR',
                color: '#dc3545',
                message: 'Erro no processamento ETL',
                details: result.error
            });
        }
        
    } catch (error) {
        addLogMessage({
            timestamp: new Date().toLocaleString('pt-BR'),
            level: 'CRITICAL',
            color: '#6f42c1',
            message: 'Erro crítico no processamento',
            details: error.toString()
        });
    } finally {
        // Reset process button
        processBtn.disabled = false;
        updateProcessButton();
        
        // Hide progress section after delay
        setTimeout(() => {
            progressSection.style.display = 'none';
            updateProgress('Preparando...', 0);
        }, 3000);
    }
}

function updateProgress(text, percent) {
    const progressText = document.getElementById('progressText');
    const progressPercent = document.getElementById('progressPercent');
    const progressFill = document.getElementById('progressFill');
    
    progressText.textContent = text;
    progressPercent.textContent = `${percent}%`;
    progressFill.style.width = `${percent}%`;
}

function addLogMessage(logEntry) {
    logs.push(logEntry);
    
    // Apply current filter
    if (currentFilter === 'all' || currentFilter === logEntry.level) {
        displayLogEntry(logEntry);
    }
    
    // Auto-scroll to bottom
    const logTerminal = document.getElementById('logTerminal');
    logTerminal.scrollTop = logTerminal.scrollHeight;
}

function displayLogEntry(logEntry) {
    const logTerminal = document.getElementById('logTerminal');
    
    // Remove welcome message if it exists
    const welcome = logTerminal.querySelector('.log-welcome');
    if (welcome) {
        welcome.remove();
    }
    
    // Create log entry element
    const logElement = document.createElement('div');
    logElement.className = 'log-entry';
    
    logElement.innerHTML = `
        <span class="log-timestamp">${logEntry.timestamp}</span>
        <span class="log-level ${logEntry.level}" style="color: ${logEntry.color}">${logEntry.level}</span>
        <div class="log-content">
            <div class="log-message ${logEntry.level}" style="color: ${logEntry.color}">${logEntry.message}</div>
            ${logEntry.details ? `<div class="log-details">${logEntry.details}</div>` : ''}
        </div>
    `;
    
    logTerminal.appendChild(logElement);
}

function filterLogs() {
    const logTerminal = document.getElementById('logTerminal');
    logTerminal.innerHTML = '';
    
    if (logs.length === 0) {
        logTerminal.innerHTML = `
            <div class="log-welcome">
                <i class="fas fa-info-circle"></i>
                <p>Terminal de logs pronto. Selecione os arquivos e inicie o processamento.</p>
            </div>
        `;
        return;
    }
    
    const filteredLogs = currentFilter === 'all' 
        ? logs 
        : logs.filter(log => log.level === currentFilter);
    
    if (filteredLogs.length === 0) {
        logTerminal.innerHTML = `
            <div class="log-welcome">
                <i class="fas fa-filter"></i>
                <p>Nenhum log encontrado para o filtro selecionado.</p>
            </div>
        `;
        return;
    }
    
    filteredLogs.forEach(log => displayLogEntry(log));
}

function clearLogs() {
    logs = [];
    const logTerminal = document.getElementById('logTerminal');
    logTerminal.innerHTML = `
        <div class="log-welcome">
            <i class="fas fa-info-circle"></i>
            <p>Terminal de logs limpo. Pronto para novos logs.</p>
        </div>
    `;
}

function exportLogs() {
    if (logs.length === 0) {
        addLogMessage({
            timestamp: new Date().toLocaleString('pt-BR'),
            level: 'WARNING',
            color: '#ffc107',
            message: 'Nenhum log disponível para exportação',
            details: ''
        });
        return;
    }
    
    const logText = logs.map(log => {
        let text = `[${log.timestamp}] ${log.level}: ${log.message}`;
        if (log.details) {
            text += `\n    Detalhes: ${log.details}`;
        }
        return text;
    }).join('\n\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `etl_logs_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    addLogMessage({
        timestamp: new Date().toLocaleString('pt-BR'),
        level: 'SUCCESS',
        color: '#28a745',
        message: 'Logs exportados com sucesso',
        details: `Arquivo: ${a.download}`
    });
}

function showResults(result) {
    const resultsContent = document.getElementById('resultsContent');
    
    const stats = result.results;
    
    resultsContent.innerHTML = `
        <div class="results-grid">
            <div class="result-item">
                <span class="result-label">Status:</span>
                <span class="result-value" style="color: #28a745;">✓ Sucesso</span>
            </div>
            <div class="result-item">
                <span class="result-label">Banco de Dados:</span>
                <span class="result-value">${result.database_path}</span>
            </div>
            ${stats.extraction ? `
                <div class="result-item">
                    <span class="result-label">Registros Extraídos (Saldos):</span>
                    <span class="result-value">${stats.extraction.saldos_rows.toLocaleString('pt-BR')}</span>
                </div>
                <div class="result-item">
                    <span class="result-label">Registros Extraídos (Resgates):</span>
                    <span class="result-value">${stats.extraction.resgates_rows.toLocaleString('pt-BR')}</span>
                </div>
            ` : ''}
            ${stats.transformation ? `
                <div class="result-item">
                    <span class="result-label">Contas Únicas:</span>
                    <span class="result-value">${stats.transformation.dim_contas_rows.toLocaleString('pt-BR')}</span>
                </div>
                <div class="result-item">
                    <span class="result-label">Registros de Saldos:</span>
                    <span class="result-value">${stats.transformation.fact_saldos_rows.toLocaleString('pt-BR')}</span>
                </div>
                <div class="result-item">
                    <span class="result-label">Registros de Resgates:</span>
                    <span class="result-value">${stats.transformation.fact_resgates_rows.toLocaleString('pt-BR')}</span>
                </div>
            ` : ''}
            ${stats.load ? `
                <div class="result-item">
                    <span class="result-label">Total de Registros no Banco:</span>
                    <span class="result-value">${stats.load.total_records.toLocaleString('pt-BR')}</span>
                </div>
            ` : ''}
        </div>
    `;
    
    openModal('resultsModal');
}

function loadDatabaseConfig() {
    // This would load current database configuration
    // For now, we'll set defaults
    document.getElementById('dbType').value = 'sqlite';
    updateDatabaseConfig();
}

function updateDatabaseConfig() {
    const dbType = document.getElementById('dbType').value;
    const dbConfig = document.getElementById('dbConfig');
    
    let configHTML = '';
    
    switch (dbType) {
        case 'sqlite':
            configHTML = `
                <div class="form-group">
                    <label for="dbPath">Caminho do Banco:</label>
                    <input type="text" id="dbPath" class="form-control" value="./output/contas_judiciais.db">
                </div>
            `;
            break;
        case 'postgresql':
            configHTML = `
                <div class="form-group">
                    <label for="dbHost">Host:</label>
                    <input type="text" id="dbHost" class="form-control" value="localhost">
                </div>
                <div class="form-group">
                    <label for="dbPort">Porta:</label>
                    <input type="number" id="dbPort" class="form-control" value="5432">
                </div>
                <div class="form-group">
                    <label for="dbName">Nome do Banco:</label>
                    <input type="text" id="dbName" class="form-control" value="etl_database">
                </div>
                <div class="form-group">
                    <label for="dbUser">Usuário:</label>
                    <input type="text" id="dbUser" class="form-control" value="postgres">
                </div>
                <div class="form-group">
                    <label for="dbPassword">Senha:</label>
                    <input type="password" id="dbPassword" class="form-control">
                </div>
            `;
            break;
        case 'mysql':
            configHTML = `
                <div class="form-group">
                    <label for="dbHost">Host:</label>
                    <input type="text" id="dbHost" class="form-control" value="localhost">
                </div>
                <div class="form-group">
                    <label for="dbPort">Porta:</label>
                    <input type="number" id="dbPort" class="form-control" value="3306">
                </div>
                <div class="form-group">
                    <label for="dbName">Nome do Banco:</label>
                    <input type="text" id="dbName" class="form-control" value="etl_database">
                </div>
                <div class="form-group">
                    <label for="dbUser">Usuário:</label>
                    <input type="text" id="dbUser" class="form-control" value="root">
                </div>
                <div class="form-group">
                    <label for="dbPassword">Senha:</label>
                    <input type="password" id="dbPassword" class="form-control">
                </div>
            `;
            break;
        case 'sqlserver':
            configHTML = `
                <div class="form-group">
                    <label for="dbHost">Host:</label>
                    <input type="text" id="dbHost" class="form-control" value="localhost">
                </div>
                <div class="form-group">
                    <label for="dbPort">Porta:</label>
                    <input type="number" id="dbPort" class="form-control" value="1433">
                </div>
                <div class="form-group">
                    <label for="dbName">Nome do Banco:</label>
                    <input type="text" id="dbName" class="form-control" value="etl_database">
                </div>
                <div class="form-group">
                    <label for="dbUser">Usuário:</label>
                    <input type="text" id="dbUser" class="form-control" value="sa">
                </div>
                <div class="form-group">
                    <label for="dbPassword">Senha:</label>
                    <input type="password" id="dbPassword" class="form-control">
                </div>
            `;
            break;
    }
    
    dbConfig.innerHTML = configHTML;
}

async function saveConfig() {
    const dbType = document.getElementById('dbType').value;
    
    let config = { type: dbType };
    
    switch (dbType) {
        case 'sqlite':
            config.path = document.getElementById('dbPath').value;
            break;
        case 'postgresql':
        case 'mysql':
        case 'sqlserver':
            config.host = document.getElementById('dbHost').value;
            config.port = parseInt(document.getElementById('dbPort').value);
            config.database = document.getElementById('dbName').value;
            config.username = document.getElementById('dbUser').value;
            config.password = document.getElementById('dbPassword').value;
            break;
    }
    
    try {
        await eel.update_database_config(config)();
        
        addLogMessage({
            timestamp: new Date().toLocaleString('pt-BR'),
            level: 'SUCCESS',
            color: '#28a745',
            message: 'Configuração de banco de dados atualizada',
            details: `Tipo: ${dbType}`
        });
        
        closeModal('configModal');
    } catch (error) {
        addLogMessage({
            timestamp: new Date().toLocaleString('pt-BR'),
            level: 'ERROR',
            color: '#dc3545',
            message: 'Erro ao salvar configuração',
            details: error.toString()
        });
    }
}

function openModal(modalId) {
    document.getElementById(modalId).style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Eel callback functions (chamadas pelo backend Python)
eel.expose(add_log_message);
function add_log_message(logEntry) {
    addLogMessage(logEntry);
}

eel.expose(update_progress);
function update_progress_callback(step, progress) {
    updateProgress(step, progress);
}

eel.expose(clear_logs);
function clear_logs_callback() {
    clearLogs();
}

