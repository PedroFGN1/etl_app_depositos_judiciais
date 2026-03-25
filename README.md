# Sistema ETL - Extratos Bancarios em PDF

Aplicacao ETL com interface web para processamento de extratos bancarios em PDF, com suporte atual para `CAIXA` e `BB`.

O sistema extrai dados do PDF, aplica regras de classificacao por banco e grava o resultado em tabelas separadas no banco de dados configurado.

## Visao geral

Estado atual do projeto:

- entrada unica: `1` PDF de extrato bancario
- selecao explicita do banco na interface: `CAIXA` ou `BB`
- regras dirigidas por `output/regras_extrato.json`
- schema transformado unificado para os bancos
- carga em tabelas `Movimentacoes_<BANCO>`
- interface com upload, progresso, logs e configuracao de banco

No fluxo do Banco do Brasil, linhas de saldo tambem viram registros proprios com `Historico = SALDO DIARIO`.

## Funcionalidades

- Interface web com Eel
- Upload de PDF via drag-and-drop
- Pipeline ETL modularizado em `extract`, `transform` e `load`
- Regras configuraveis por banco
- Suporte a SQLite, PostgreSQL, MySQL e SQL Server
- Logs em tempo real com filtro por nivel
- Exportacao de logs pela interface
- Testes automatizados para regras, extratores, transformacao e pipeline

## Estrutura do projeto

```text
etl_app_depositos_judiciais/
|-- backend/
|   |-- __init__.py
|   |-- config.py
|   |-- logger.py
|   |-- rules_engine.py
|   |-- extractor.py
|   |-- transformer.py
|   |-- loader.py
|   |-- etl_pipeline.py
|   `-- eel_interface.py
|-- frontend/
|   |-- index.html
|   |-- styles.css
|   `-- app.js
|-- data_samples/
|-- docs/
|-- output/
|   `-- regras_extrato.json
|-- uploads/
|-- main.py
|-- requirements.txt
|-- test_etl.py
`-- README.md
```

## Arquitetura

O fluxo principal funciona assim:

1. O usuario seleciona o banco e envia o PDF do extrato.
2. A interface envia o arquivo para o backend via Eel.
3. O `RulesEngine` carrega as regras do banco escolhido.
4. O `ExtractorFactory` instancia o extrator apropriado:
   - `CaixaExtractor`
   - `BBExtractor`
5. O `DataTransformer` padroniza e classifica os registros.
6. O `DataLoader` persiste o resultado na tabela do banco correspondente.

Tabelas de destino:

- `Movimentacoes_CAIXA`
- `Movimentacoes_BB`

## Schema de saida

O resultado transformado segue um schema comum:

- `Data`
- `Documento`
- `Historico`
- `Valor`
- `Tipo_Valor`
- `Saldo`
- `Tipo_Saldo`
- `Natureza_Operacao`
- `Banco`
- `Pagina`
- `Linha`

Convencoes atuais:

- movimentacoes usam `Valor` e `Tipo_Valor`
- eventos de saldo do BB usam `Saldo` e `Tipo_Saldo`
- linhas de saldo do BB recebem `Historico = SALDO DIARIO`

## Bancos suportados

### CAIXA

- extracao stateless
- data completa presente na propria linha
- classificacao baseada em rubricas configuradas

### BB

- extracao stateful
- movimentacoes usam data curta `DD.MM`
- linhas `Saldo em DD.MM.AAAA ...` atualizam a memoria de ano
- essas mesmas linhas tambem geram registros independentes de saldo diario

## Regras de extracao e classificacao

As regras ficam em:

```text
output/regras_extrato.json
```

Cada banco possui:

- `padrao_linha_movimento`
- `formato_data`
- `rubricas`
- `padrao_linha_saldo`, quando aplicavel

Exemplo de rubrica especial do BB:

- `SALDO DIARIO -> Saldo Atualizado`

Importante:

- o matching de rubricas depende do texto real extraido do PDF
- variacoes de acentuacao podem exigir ajuste no arquivo de regras

## Requisitos

- Python 3.10+ recomendado
- dependencias do `requirements.txt`

Principais pacotes:

- `eel`
- `pandas`
- `sqlalchemy`
- `pdfplumber`
- `psutil`

Drivers opcionais:

- PostgreSQL: `psycopg2-binary`
- MySQL: `PyMySQL`
- SQL Server: `pyodbc`

## Instalacao

### 1. Criar ambiente virtual

No Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 3. Executar a aplicacao

```powershell
python main.py
```

Observacao:

- a aplicacao usa Eel
- `config.EEL_PORT` esta em `0`, entao a porta final pode ser dinamica
- use o endereco exibido no terminal ao iniciar

## Como usar

1. Execute `python main.py`.
2. Abra a interface no endereco informado pelo terminal.
3. Selecione o banco do extrato:
   - `CAIXA`
   - `BB`
4. Envie o PDF.
5. Clique em `Iniciar Processamento ETL`.
6. Acompanhe os logs e o progresso.
7. Consulte o modal final com banco, tabela e quantidade de registros.

## Configuracao de banco de dados

Tipos suportados:

- SQLite
- PostgreSQL
- MySQL
- SQL Server

### SQLite

Configuracao padrao:

```python
config.set_database_config("sqlite", path="./output/contas_judiciais.db")
```

### PostgreSQL

```python
config.set_database_config(
    "postgresql",
    host="localhost",
    port=5432,
    database="etl_db",
    username="postgres",
    password="senha",
)
```

### MySQL

```python
config.set_database_config(
    "mysql",
    host="localhost",
    port=3306,
    database="etl_db",
    username="root",
    password="senha",
)
```

### SQL Server

```python
config.set_database_config(
    "sqlserver",
    host="localhost",
    port=1433,
    database="etl_db",
    username="sa",
    password="senha",
)
```

Tambem e possivel alterar a configuracao diretamente pela interface em `Configuracoes`.

## Logs

Niveis disponiveis:

- `DEBUG`
- `INFO`
- `SUCCESS`
- `WARNING`
- `ERROR`
- `CRITICAL`

Exemplos de eventos logados:

- validacao do PDF
- carregamento das regras
- linhas de saldo identificadas no BB
- linhas ignoradas por nao casarem com o layout
- estatisticas de transformacao
- resultado da carga no banco

## Testes

Para executar a suite automatizada:

```powershell
python -m unittest -v test_etl.py
```

Cobertura atual:

- carregamento e validacao das regras multi-banco
- `ExtractorFactory`
- virada de ano do `BBExtractor`
- evento `SALDO DIARIO`
- transformacao do schema unificado
- smoke test da CAIXA
- falha controlada quando o layout nao corresponde ao banco selecionado

## Solucao de problemas

### O PDF nao e aceito

Verifique:

- se o arquivo tem extensao `.pdf`
- se `pdfplumber` esta instalado

### O processamento falha no BB

Verifique:

- se o banco selecionado e realmente `BB`
- se `padrao_linha_movimento` e `padrao_linha_saldo` refletem o layout atual do PDF
- se as rubricas do BB no JSON batem com o texto extraido

### Muitas linhas saem como `Desconhecido`

Atualize as rubricas em `output/regras_extrato.json`.

### Erro de conexao com banco

Verifique:

- credenciais
- driver instalado
- acesso de rede
- permissao para criar ou substituir tabelas

## Arquivos importantes

- `main.py`: ponto de entrada
- `backend/etl_pipeline.py`: orquestracao do ETL
- `backend/extractor.py`: extratores por banco
- `backend/rules_engine.py`: regras de extracao e classificacao
- `backend/transformer.py`: padronizacao do schema
- `backend/loader.py`: carga no banco
- `output/regras_extrato.json`: regras runtime
- `test_etl.py`: testes automatizados

## Documentacao complementar

- `Sistema ETL - Instruções de Instalação e Uso.md`
- arquivos em `docs/`

---
