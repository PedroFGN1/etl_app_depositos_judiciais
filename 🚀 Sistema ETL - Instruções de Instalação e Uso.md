# 🚀 Sistema ETL - Instruções de Instalação e Uso

## 📋 Resumo do Projeto

Foi criado um sistema ETL completo com interface web moderna para processamento de dados judiciais, baseado no código Python original fornecido. O sistema inclui:

### ✨ Características Principais

- **Frontend Responsivo**: Interface web moderna com upload drag-and-drop
- **Terminal de Logs Colorido**: Logs em tempo real com diferentes cores por nível
- **Backend Modularizado**: Código Python organizado em módulos especializados
- **Suporte Multi-Banco**: SQLite, PostgreSQL, MySQL e SQL Server
- **Comunicação Eel**: Integração seamless entre Python e JavaScript

### 🏗️ Arquitetura

```
etl_app/
├── backend/                 # Módulos Python
│   ├── config.py           # Configurações flexíveis
│   ├── logger.py           # Sistema de logging colorido
│   ├── extractor.py        # Extração de dados
│   ├── transformer.py      # Transformação de dados
│   ├── loader.py           # Carga no banco
│   ├── etl_pipeline.py     # Orquestrador principal
│   └── eel_interface.py    # Interface Eel
├── frontend/               # Interface web
│   ├── index.html          # Página principal
│   ├── styles.css          # Estilos CSS modernos
│   └── app.js              # JavaScript
├── data_samples/           # Arquivos de exemplo
├── main.py                 # Arquivo principal
└── requirements.txt        # Dependências
```

## 🛠️ Instalação

### 1. Extrair o Projeto
```bash
unzip etl_app_completo.zip
cd etl_app
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Executar a Aplicação
```bash
python main.py
```

### 4. Acessar no Navegador
```
http://localhost:8080
```

## 📊 Como Usar

### 1. Upload de Arquivos
- **Arraste e solte** ou **clique** nas áreas de upload
- Formatos suportados: **CSV, XLSX, XLS**
- Validação automática de arquivos

### 2. Processamento ETL
- Clique em **"Iniciar Processamento ETL"**
- Acompanhe o progresso na barra de progresso
- Monitore os logs no terminal colorido

### 3. Terminal de Logs
- **DEBUG** (Cinza): Informações de depuração
- **INFO** (Azul): Informações gerais
- **SUCCESS** (Verde): Operações bem-sucedidas
- **WARNING** (Amarelo): Avisos importantes
- **ERROR** (Vermelho): Erros recuperáveis
- **CRITICAL** (Roxo): Erros críticos

### 4. Configurações
- Clique em **"Configurações"** para alterar o banco de dados
- Suporte para SQLite (padrão), PostgreSQL, MySQL e SQL Server
- Teste de conexão automático

## 🗄️ Configuração de Banco de Dados

### SQLite (Padrão)
- Não requer configuração adicional
- Banco criado automaticamente em `./output/`

### PostgreSQL
```python
# Instalar driver: pip install psycopg2-binary
# Configurar na interface web ou via código:
config.set_database_config('postgresql', 
    host='localhost',
    port=5432,
    database='etl_db',
    username='postgres',
    password='senha'
)
```

### MySQL
```python
# Instalar driver: pip install PyMySQL
config.set_database_config('mysql',
    host='localhost', 
    port=3306,
    database='etl_db',
    username='root',
    password='senha'
)
```

### SQL Server
```python
# Instalar driver: pip install pyodbc
config.set_database_config('sqlserver',
    host='localhost',
    port=1433, 
    database='etl_db',
    username='sa',
    password='senha'
)
```

## 📁 Formato dos Dados

### Arquivo de Saldos
Deve conter colunas com:
- **Conta Judicial**: Identificação da conta
- **Parcela**: Número da parcela  
- **Saldos por período**: Ex: "Saldo JANEIRO23", "Saldo FEVEREIRO23"

### Arquivo de Resgates
Deve conter colunas com:
- **Número da Conta Judicial**: Identificação da conta
- **Número da Parcela**: Número da parcela
- **Datas**: Datas de resgate e competência
- **Valores**: Valores monetários dos resgates

## 🔧 Melhorias Implementadas

### Em relação ao código original:

1. **Modularização Completa**
   - Separação em módulos especializados
   - Configuração flexível de banco de dados
   - Sistema de logging avançado

2. **Interface Web Moderna**
   - Upload drag-and-drop
   - Terminal de logs colorido
   - Feedback visual em tempo real
   - Design responsivo

3. **Robustez e Flexibilidade**
   - Suporte a múltiplos formatos de arquivo
   - Validação de dados aprimorada
   - Tratamento de erros robusto
   - Configuração de banco flexível

4. **Experiência do Usuário**
   - Progresso visual do processamento
   - Logs categorizados por cores
   - Exportação de logs
   - Modal de resultados

## 🚨 Solução de Problemas

### Erro de Dependências
```bash
pip install --upgrade -r requirements.txt
```

### Erro de Conexão com Banco
- Verifique as credenciais na configuração
- Teste a conectividade de rede
- Confirme se o driver está instalado

### Arquivos Não Reconhecidos
- Verifique o formato (CSV, XLSX, XLS)
- Confirme a codificação (UTF-8 recomendado)
- Verifique se as colunas esperadas existem

## 📈 Exemplo de Uso

1. **Inicie a aplicação**: `python main.py`
2. **Acesse**: http://localhost:8080
3. **Faça upload** dos arquivos de saldos e resgates
4. **Clique** em "Iniciar Processamento ETL"
5. **Acompanhe** os logs coloridos no terminal
6. **Visualize** os resultados no modal final

## 🎯 Resultados Esperados

Após o processamento, o sistema criará:
- **Tabela Contas**: Dimensão com contas únicas
- **Tabela Saldos**: Fatos de saldos por período
- **Tabela Resgates**: Fatos de resgates realizados

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs no terminal colorido
2. Consulte o arquivo README.md
3. Teste com os arquivos de exemplo em `data_samples/`

---

**Sistema desenvolvido com base no código ETL original, expandido com interface web moderna e funcionalidades avançadas.**

