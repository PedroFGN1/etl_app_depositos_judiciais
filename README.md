# Sistema ETL - Processamento de Dados Judiciais

Sistema completo de ETL (Extract, Transform, Load) com interface web para processamento de dados de contas judiciais.

## 🚀 Características

- **Interface Web Moderna**: Frontend responsivo com upload de arquivos e terminal de logs colorido
- **Backend Modularizado**: Código Python organizado em módulos especializados
- **Suporte Multi-Banco**: SQLite, PostgreSQL, MySQL e SQL Server
- **Logs em Tempo Real**: Terminal colorido com diferentes níveis de log
- **Comunicação Eel**: Integração seamless entre Python e JavaScript

## 📁 Estrutura do Projeto

```
etl_app/
├── backend/                # Módulos Python
│   ├── __init__.py
│   ├── config.py           # Configurações flexíveis
│   ├── logger.py           # Sistema de logging
│   ├── extractor.py        # Extração de dados
│   ├── transformer.py      # Transformação de dados
│   ├── loader.py           # Carga no banco
│   ├── etl_pipeline.py     # Orquestrador principal
│   └── eel_interface.py    # Interface Eel
├── frontend/               # Interface web
│   ├── index.html          # Página principal
│   ├── styles.css          # Estilos CSS
│   └── app.js              # JavaScript
├── data_samples/           # Arquivos de exemplo
├── uploads/                # Arquivos enviados
├── output/                 # Banco de dados gerado
├── main.py                 # Arquivo principal
├── requirements.txt        # Dependências
└── README.md               # Esta documentação
```

## 🛠️ Instalação

1. **Clone ou baixe o projeto**
2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute a aplicação:**
   ```bash
   python main.py
   ```

4. **Acesse no navegador:**
   ```
   http://localhost:8080
   ```

## 📊 Como Usar

### 1. Upload de Arquivos
- Clique ou arraste os arquivos de saldos e resgates
- Formatos suportados: CSV, XLSX, XLS
- O sistema valida automaticamente os arquivos

### 2. Processamento ETL
- Clique em "Iniciar Processamento ETL"
- Acompanhe o progresso na barra de progresso
- Monitore os logs no terminal colorido

### 3. Configuração de Banco
- Clique em "Configurações" para alterar o banco de dados
- Suporte para SQLite (padrão), PostgreSQL, MySQL e SQL Server
- Teste de conexão automático

## 🎨 Terminal de Logs

O terminal possui logs coloridos por nível:
- **DEBUG** (Cinza): Informações de depuração
- **INFO** (Azul): Informações gerais
- **SUCCESS** (Verde): Operações bem-sucedidas
- **WARNING** (Amarelo): Avisos importantes
- **ERROR** (Vermelho): Erros recuperáveis
- **CRITICAL** (Roxo): Erros críticos

## 🗄️ Configuração de Banco de Dados

### SQLite (Padrão)
```python
config.set_database_config('sqlite', path='./output/database.db')
```

### PostgreSQL
```python
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
config.set_database_config('sqlserver',
    host='localhost',
    port=1433, 
    database='etl_db',
    username='sa',
    password='senha'
)
```

## 📋 Formato dos Dados

### Arquivo de Saldos
Deve conter colunas com:
- Identificação da conta judicial
- Número da parcela  
- Colunas de saldo por período (ex: "Saldo JANEIRO23")

### Arquivo de Resgates
Deve conter colunas com:
- Número da conta judicial
- Número da parcela
- Datas de resgate
- Valores monetários

## 🔧 Desenvolvimento

### Estrutura Modular

O sistema foi desenvolvido com arquitetura modular:

- **config.py**: Configurações centralizadas e flexíveis
- **logger.py**: Sistema de logging com cores e comunicação Eel
- **extractor.py**: Extração de dados de múltiplos formatos
- **transformer.py**: Transformações e limpeza de dados
- **loader.py**: Carga em diferentes tipos de banco
- **etl_pipeline.py**: Orquestração do processo completo
- **eel_interface.py**: Comunicação entre Python e JavaScript

### Adicionando Novos Bancos

Para adicionar suporte a um novo banco:

1. Adicione a configuração em `config.py`:
```python
'novo_banco': {
    'driver': 'driver_sqlalchemy',
    'engine_template': 'driver://user:pass@host:port/db'
}
```

2. Instale o driver correspondente
3. Teste a conexão

### Personalizando Transformações

As transformações podem ser customizadas no arquivo `transformer.py`:

```python
def custom_transform(self, df: pd.DataFrame) -> pd.DataFrame:
    # Sua lógica de transformação aqui
    return df
```

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

## 📝 Logs e Debugging

- Logs são salvos em tempo real no terminal
- Use o filtro para visualizar logs específicos
- Exporte logs para arquivo quando necessário
- Nível DEBUG mostra informações detalhadas

## 🔒 Segurança

- Arquivos são salvos temporariamente durante o processamento
- Limpeza automática de arquivos temporários
- Validação de tipos de arquivo
- Sanitização de nomes de arquivo

## 📈 Performance

- Processamento otimizado com pandas
- Carregamento em lote para bancos de dados
- Validação prévia de dados
- Feedback de progresso em tempo real

## 🤝 Contribuição

Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Implemente as mudanças
4. Teste thoroughly
5. Submeta um pull request

## 📄 Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para detalhes.

## 🆘 Suporte

Para suporte técnico:
- Verifique os logs no terminal
- Consulte esta documentação
- Reporte issues com logs detalhados

