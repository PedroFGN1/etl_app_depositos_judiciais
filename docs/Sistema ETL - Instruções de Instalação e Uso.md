# Sistema ETL - Instrucoes de Instalacao e Uso

## Resumo

Esta aplicacao processa extratos bancarios em PDF por meio de um pipeline ETL com interface web baseada em Eel.

Estado atual da aplicacao:

- Entrada unica: `1` PDF de extrato bancario
- Bancos suportados: `CAIXA` e `BB`
- Extracao orientada por regras em `output/regras_extrato.json`
- Carga em tabelas separadas por banco, como `Movimentacoes_CAIXA` e `Movimentacoes_BB`
- Interface com upload do PDF, seletor de banco, barra de progresso e terminal de logs

No Banco do Brasil, linhas de saldo tambem sao tratadas como eventos proprios do extrato com `Historico = SALDO DIARIO`.

## Arquitetura

```text
etl_app_depositos_judiciais/
|-- backend/
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
|-- output/
|   `-- regras_extrato.json
|-- uploads/
|-- main.py
|-- requirements.txt
`-- test_etl.py
```

## Como o fluxo funciona

1. O usuario envia um PDF pela interface e escolhe o banco do extrato.
2. O backend salva o arquivo temporariamente.
3. O `RulesEngine` carrega as regras do banco selecionado.
4. O `ExtractorFactory` instancia o extrator correto:
   - `CaixaExtractor`: leitura stateless linha a linha
   - `BBExtractor`: leitura stateful com controle de ano e saldo diario
5. O `DataTransformer` padroniza o schema e classifica os historicos.
6. O `DataLoader` grava o resultado na tabela do banco correspondente.

## Schema de saida

As tabelas carregadas no banco seguem o schema unificado:

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

Comportamento por tipo de linha:

- Movimentacoes: `Valor` e `Tipo_Valor` preenchidos
- Eventos de saldo do BB: `Saldo` e `Tipo_Saldo` preenchidos, com `Historico = SALDO DIARIO`

## Instalacao

### 1. Criar e ativar ambiente virtual

Exemplo no Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias

```powershell
pip install -r requirements.txt
```

Dependencias principais:

- `eel`
- `pandas`
- `sqlalchemy`
- `pdfplumber`
- `psutil`

Drivers de banco opcionais:

- PostgreSQL: `psycopg2-binary`
- MySQL: `PyMySQL`
- SQL Server: `pyodbc`

## Execucao

### Interface web

```powershell
python main.py
```

Ao iniciar:

- a aplicacao verifica dependencias
- garante a criacao dos diretorios necessarios
- inicia o frontend via Eel

Observacao:

- `config.EEL_PORT` esta definido como `0`, entao a porta pode ser escolhida dinamicamente pelo runtime
- use o endereco exibido nos logs ao iniciar a aplicacao

### Teste automatizado

```powershell
python -m unittest -v test_etl.py
```

## Como usar a interface

1. Inicie a aplicacao com `python main.py`.
2. Abra a interface no endereco informado pelos logs.
3. Selecione o banco do extrato:
   - `CAIXA`
   - `BB`
4. Envie o PDF do extrato.
5. Clique em `Iniciar Processamento ETL`.
6. Acompanhe o progresso e os logs.
7. Ao final, consulte o modal de resultados com banco, tabela e quantidade de registros.

## Regras por banco

As regras ficam em `output/regras_extrato.json`.

Cada banco possui:

- `padrao_linha_movimento`
- `formato_data`
- `rubricas`
- `padrao_linha_saldo` quando aplicavel

### CAIXA

- Processamento orientado a movimentacoes com data completa na propria linha
- Tabela de destino: `Movimentacoes_CAIXA`

### BB

- Processamento stateful com data `DD.MM` nas movimentacoes
- Uso das linhas `Saldo em DD.MM.AAAA ...` para:
  - atualizar o ano corrente
  - gerar registros independentes de saldo diario
- Tabela de destino: `Movimentacoes_BB`

Rubricas comuns do BB no estado atual:

- `ATUALIZACAO DE REC APLICADOS`
- `EFETIVACAO DE RESGATE EM FUNDO GARA` ou variante conforme o PDF
- `RECOMPOSICAO DE FUNDO GARANTIDOR`
- `SALDO DIARIO`

Importante:

- o matching de rubricas depende do texto extraido do PDF
- diferencas de acentuacao podem exigir ajuste no arquivo de regras

## Banco de dados

Tipos suportados:

- SQLite
- PostgreSQL
- MySQL
- SQL Server

### SQLite

Configuracao padrao:

- arquivo: `./output/contas_judiciais.db`

### Configuracao pela interface

Na tela `Configuracoes`, e possivel:

- trocar o tipo de banco
- informar host, porta, nome, usuario e senha quando necessario
- validar a conexao antes do processamento

## Logs e monitoramento

Niveis disponiveis na interface:

- `DEBUG`
- `INFO`
- `SUCCESS`
- `WARNING`
- `ERROR`
- `CRITICAL`

Exemplos de eventos registrados:

- validacao do PDF
- carregamento das regras
- identificacao de linhas de saldo do BB
- linhas ignoradas por nao corresponderem ao layout esperado
- transformacao e carga no banco

Os logs podem ser exportados pela propria interface.

## Resultados esperados

Ao concluir um processamento com sucesso, a aplicacao retorna:

- banco processado
- tabela de destino
- caminho do banco configurado
- quantidade de linhas extraidas
- quantidade de linhas classificadas
- quantidade de linhas classificadas como `Desconhecido`

## Solucao de problemas

### O PDF nao processa

Verifique:

- se o arquivo enviado e realmente `.pdf`
- se o banco selecionado corresponde ao layout do extrato
- se `pdfplumber` esta instalado

### O BB falha por layout incompatível

Causas comuns:

- `padrao_linha_movimento` ou `padrao_linha_saldo` nao condizem com o PDF atual
- a linha de saldo do BB mudou de formato
- a rubrica no PDF nao bate com o mapeamento configurado

Arquivo para ajuste:

- `output/regras_extrato.json`

### Muitas linhas classificadas como `Desconhecido`

Atualize as rubricas do banco correspondente em `output/regras_extrato.json`.

### Erro de conexao com banco

Verifique:

- credenciais
- driver instalado
- conectividade de rede
- permissao para criar ou atualizar tabelas

## Arquivos importantes

- `main.py`: ponto de entrada da aplicacao
- `backend/etl_pipeline.py`: orquestracao do ETL
- `backend/extractor.py`: extratores CAIXA e BB
- `backend/rules_engine.py`: carga e validacao das regras
- `output/regras_extrato.json`: regras runtime por banco
- `test_etl.py`: testes automatizados do fluxo

## Validacao atual do projeto

O projeto possui testes cobrindo:

- carregamento das regras multi-banco
- `ExtractorFactory`
- virada de ano no `BBExtractor`
- evento `SALDO DIARIO`
- transformacao do schema unificado
- smoke test da CAIXA
- falha quando o layout nao corresponde ao banco selecionado

---
