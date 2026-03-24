// Global variables
let uploadedFiles = {
    extrato: null
};

let currentFilter = 'all';
let logs = [];

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupSinglePdfMode();
    setupFileUploads();
    setupEventListeners();
    setupLogFilter();

    addLogMessage({
        timestamp: new Date().toLocaleString('pt-BR'),
        level: 'INFO',
        color: '#17a2b8',
        message: 'Sistema ETL inicializado. Aguardando o PDF do extrato para processamento.',
        details: ''
    });
}

function setupSinglePdfMode() {
    const uploadHeaders = document.querySelectorAll('.upload-header h3');
    if (uploadHeaders[0]) uploadHeaders[0].textContent = 'PDF do Extrato';
    if (uploadHeaders[1]) uploadHeaders[1].textContent = 'Slot desativado';

    const placeholders = document.querySelectorAll('.upload-placeholder p');
    if (placeholders[0]) placeholders[0].textContent = 'Clique ou arraste o PDF do extrato aqui';
    if (placeholders[1]) placeholders[1].textContent = 'Este slot nao e usado no novo fluxo';

    const hints = document.querySelectorAll('.upload-placeholder small');
    if (hints[0]) hints[0].textContent = 'Formato aceito: PDF';
    if (hints[1]) hints[1].textContent = 'Nenhum arquivo necessario';

    const sectionHeader = document.querySelector('.upload-section .section-header p');
    if (sectionHeader) sectionHeader.textContent = 'Selecione o PDF de extrato para processamento ETL';

    const resgatesCard = document.querySelectorAll('.upload-card')[1];
    if (resgatesCard) {
        resgatesCard.style.opacity = '0.45';
        resgatesCard.style.pointerEvents = 'none';
    }

    const resgatesInput = document.getElementById('resgatesFile');
    if (resgatesInput) resgatesInput.disabled = true;
}

function setupFileUploads() {
    setupFileUpload('saldos', 'extrato');
}

function setupFileUpload(domType, logicalType) {
    const uploadArea = document.getElementById(`${domType}Upload`);
    const fileInput = document.getElementById(`${domType}File`);
    if (!uploadArea || !fileInput) return;

    fileInput.setAttribute('accept', '.pdf');

    uploadArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        handleFileSelect(logicalType, domType, e.target.files[0]);
    });

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
            handleFileSelect(logicalType, domType, files[0]);
        }
    });
}

function handleFileSelect(logicalType, domType, file) {
    if (!file) return;

    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    if (fileExtension !== '.pdf') {
        addLogMessage({
            timestamp: new Date().toLocaleString('pt-BR'),
            level: 'ERROR',
            color: '#dc3545',
            message: `Formato de arquivo nao suportado: ${fileExtension}`,
            details: 'Formato aceito: .pdf'
        });
        return;
    }

    const reader = new FileReader();
    reader.onload = async function(event) {
        const base64data = event.target.result.split(',')[1];
        const uploadResult = await eel.upload_file(file.name, base64data)();

        if (uploadResult.success) {
            uploadedFiles[logicalType] = file;
            updateFileInfo(domType, file);
            updateProcessButton();

            addLogMessage({
                timestamp: new Date().toLocaleString('pt-BR'),
                level: 'SUCCESS',
                color: '#28a745',
                message: `PDF carregado e enviado: ${file.name}`,
                details: `Tamanho: ${formatFileSize(file.size)}`
            });
        } else {
            addLogMessage({
                timestamp: new Date().toLocaleString('pt-BR'),
                level: 'ERROR',
                color: '#dc3545',
                message: `Erro ao enviar PDF: ${file.name}`,
                details: uploadResult.error
            });
        }
    };

    reader.readAsDataURL(file);
}

function updateFileInfo(domType, file) {
    const uploadArea = document.getElementById(`${domType}Upload`);
    const fileInfo = document.getElementById(`${domType}Info`);

    uploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';

    fileInfo.querySelector('.file-name').textContent = file.name;
    fileInfo.querySelector('.file-size').textContent = formatFileSize(file.size);
}

async function removeFile(type) {
    const logicalType = type === 'saldos' ? 'extrato' : type;
    const fileToRemove = uploadedFiles[logicalType];
    if (!fileToRemove) return;

    const deleteResult = await eel.delete_uploaded_file(fileToRemove.name)();
    if (!deleteResult.success) {
        addLogMessage({
            timestamp: new Date().toLocaleString('pt-BR'),
            level: 'ERROR',
            color: '#dc3545',
            message: `Erro ao remover PDF: ${fileToRemove.name}`,
            details: deleteResult.error
        });
        return;
    }

    resetSelectedFile();

    addLogMessage({
        timestamp: new Date().toLocaleString('pt-BR'),
        level: 'INFO',
        color: '#17a2b8',
        message: 'PDF removido',
        details: ''
    });
}

function resetSelectedFile() {
    uploadedFiles.extrato = null;

    const uploadArea = document.getElementById('saldosUpload');
    const fileInfo = document.getElementById('saldosInfo');
    const fileInput = document.getElementById('saldosFile');

    uploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
    fileInput.value = '';
    updateProcessButton();
}

function updateProcessButton() {
    const processBtn = document.getElementById('processBtn');
    const hasPdf = uploadedFiles.extrato;

    processBtn.disabled = !hasPdf;
    processBtn.innerHTML = hasPdf
        ? '<i class="fas fa-play"></i> Iniciar Processamento ETL'
        : '<i class="fas fa-upload"></i> Selecione o PDF primeiro';
}

function setupEventListeners() {
    document.getElementById('processBtn').addEventListener('click', startETLProcess);
    document.getElementById('clearLogsBtn').addEventListener('click', clearLogs);
    document.getElementById('configBtn').addEventListener('click', () => {
        openModal('configModal');
        loadDatabaseConfig();
    });
    document.getElementById('exportLogsBtn').addEventListener('click', exportLogs);
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
    if (!uploadedFiles.extrato) {
        addLogMessage({
            timestamp: new Date().toLocaleString('pt-BR'),
            level: 'ERROR',
            color: '#dc3545',
            message: 'Selecione o PDF do extrato antes de iniciar o processamento',
            details: ''
        });
        return;
    }

    const processBtn = document.getElementById('processBtn');
    processBtn.disabled = true;
    processBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';

    const progressSection = document.getElementById('progressSection');
    progressSection.style.display = 'block';

    try {
        clearLogs();
        addLogMessage({
            timestamp: new Date().toLocaleString('pt-BR'),
            level: 'INFO',
            color: '#17a2b8',
            message: 'Iniciando processamento ETL...',
            details: 'Preparando PDF do extrato'
        });

        const result = await eel.start_etl_process(uploadedFiles.extrato.name)();
        if (result.success) {
            updateProgress('Processamento concluido', 100);
            addLogMessage({
                timestamp: new Date().toLocaleString('pt-BR'),
                level: 'SUCCESS',
                color: '#28a745',
                message: 'Processamento ETL concluido com sucesso!',
                details: `Banco de dados: ${result.database_path}`
            });
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
            message: 'Erro critico no processamento',
            details: error.toString()
        });
    } finally {
        processBtn.disabled = false;
        resetSelectedFile();

        setTimeout(() => {
            progressSection.style.display = 'none';
            updateProgress('Preparando...', 0);
        }, 3000);
    }
}

function updateProgress(text, percent) {
    document.getElementById('progressText').textContent = text;
    document.getElementById('progressPercent').textContent = `${percent}%`;
    document.getElementById('progressFill').style.width = `${percent}%`;
}

function addLogMessage(logEntry) {
    logs.push(logEntry);

    if (currentFilter === 'all' || currentFilter === logEntry.level) {
        displayLogEntry(logEntry);
    }

    const logTerminal = document.getElementById('logTerminal');
    logTerminal.scrollTop = logTerminal.scrollHeight;
}

function displayLogEntry(logEntry) {
    const logTerminal = document.getElementById('logTerminal');
    const welcome = logTerminal.querySelector('.log-welcome');
    if (welcome) welcome.remove();

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
                <p>Terminal de logs pronto. Selecione o PDF e inicie o processamento.</p>
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
    document.getElementById('logTerminal').innerHTML = `
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
            message: 'Nenhum log disponivel para exportacao',
            details: ''
        });
        return;
    }

    const logText = logs.map(log => {
        let text = `[${log.timestamp}] ${log.level}: ${log.message}`;
        if (log.details) text += `\n    Detalhes: ${log.details}`;
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
    const stats = result.results || {};

    resultsContent.innerHTML = `
        <div class="results-grid">
            <div class="result-item">
                <span class="result-label">Status:</span>
                <span class="result-value" style="color: #28a745;">Sucesso</span>
            </div>
            <div class="result-item">
                <span class="result-label">Banco de Dados:</span>
                <span class="result-value">${result.database_path}</span>
            </div>
            ${stats.extraction ? `
                <div class="result-item">
                    <span class="result-label">Movimentacoes Extraidas:</span>
                    <span class="result-value">${stats.extraction.rows.toLocaleString('pt-BR')}</span>
                </div>
            ` : ''}
            ${stats.transformation ? `
                <div class="result-item">
                    <span class="result-label">Classificadas:</span>
                    <span class="result-value">${stats.transformation.classified_rows.toLocaleString('pt-BR')}</span>
                </div>
                <div class="result-item">
                    <span class="result-label">Desconhecidas:</span>
                    <span class="result-value">${stats.transformation.unknown_rows.toLocaleString('pt-BR')}</span>
                </div>
            ` : ''}
            ${stats.load ? `
                <div class="result-item">
                    <span class="result-label">Tabela Carregada:</span>
                    <span class="result-value">${stats.load.table_name}</span>
                </div>
                <div class="result-item">
                    <span class="result-label">Total de Registros:</span>
                    <span class="result-value">${stats.load.total_records.toLocaleString('pt-BR')}</span>
                </div>
            ` : ''}
        </div>
    `;

    openModal('resultsModal');
}

function loadDatabaseConfig() {
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
                <div class="form-group"><label for="dbHost">Host:</label><input type="text" id="dbHost" class="form-control" value="localhost"></div>
                <div class="form-group"><label for="dbPort">Porta:</label><input type="number" id="dbPort" class="form-control" value="5432"></div>
                <div class="form-group"><label for="dbName">Nome do Banco:</label><input type="text" id="dbName" class="form-control" value="etl_database"></div>
                <div class="form-group"><label for="dbUser">Usuario:</label><input type="text" id="dbUser" class="form-control" value="postgres"></div>
                <div class="form-group"><label for="dbPassword">Senha:</label><input type="password" id="dbPassword" class="form-control"></div>
            `;
            break;
        case 'mysql':
            configHTML = `
                <div class="form-group"><label for="dbHost">Host:</label><input type="text" id="dbHost" class="form-control" value="localhost"></div>
                <div class="form-group"><label for="dbPort">Porta:</label><input type="number" id="dbPort" class="form-control" value="3306"></div>
                <div class="form-group"><label for="dbName">Nome do Banco:</label><input type="text" id="dbName" class="form-control" value="etl_database"></div>
                <div class="form-group"><label for="dbUser">Usuario:</label><input type="text" id="dbUser" class="form-control" value="root"></div>
                <div class="form-group"><label for="dbPassword">Senha:</label><input type="password" id="dbPassword" class="form-control"></div>
            `;
            break;
        case 'sqlserver':
            configHTML = `
                <div class="form-group"><label for="dbHost">Host:</label><input type="text" id="dbHost" class="form-control" value="localhost"></div>
                <div class="form-group"><label for="dbPort">Porta:</label><input type="number" id="dbPort" class="form-control" value="1433"></div>
                <div class="form-group"><label for="dbName">Nome do Banco:</label><input type="text" id="dbName" class="form-control" value="etl_database"></div>
                <div class="form-group"><label for="dbUser">Usuario:</label><input type="text" id="dbUser" class="form-control" value="sa"></div>
                <div class="form-group"><label for="dbPassword">Senha:</label><input type="password" id="dbPassword" class="form-control"></div>
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
            message: 'Configuracao de banco de dados atualizada',
            details: `Tipo: ${dbType}`
        });
        closeModal('configModal');
    } catch (error) {
        addLogMessage({
            timestamp: new Date().toLocaleString('pt-BR'),
            level: 'ERROR',
            color: '#dc3545',
            message: 'Erro ao salvar configuracao',
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

eel.expose(add_log_message);
function add_log_message(logEntry) {
    addLogMessage(logEntry);
}

eel.expose(update_progress_callback);
function update_progress_callback(step, progress) {
    updateProgress(step, progress);
}

eel.expose(clear_logs);
function clear_logs() {
    clearLogs();
}
