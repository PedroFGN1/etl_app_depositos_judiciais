# Arquitetura Multi-Banco para Extratos PDF

## Resumo
Implementar suporte a `CAIXA` e `BB` com seleção explícita do banco no frontend, regras dirigidas por `regras_extrato.json`, extração via Strategy/Factory e carga em tabelas separadas por banco.
Adotar schema transformado unificado para ambos os bancos; quando o BB não trouxer saldo por linha, preencher `Saldo` e `Tipo_Saldo` com `null`.
Validar incompatibilidade entre banco selecionado e layout do PDF como erro de negócio com mensagem clara e interrupção do pipeline.

## Mudanças principais
- `RulesEngine`
  - Migrar `output/regras_extrato.json` para raiz por banco, incluindo `padrao_linha_movimento`, `padrao_linha_saldo` quando aplicável, `formato_data` e `rubricas`.
  - Validar estrutura por banco e normalizar nomes de bancos e rubricas.
  - Expor um método para retornar apenas a configuração do banco solicitado; o pipeline não deve trabalhar com regras de outros bancos.
  - Se o arquivo não existir, gerar um default multi-banco com `CAIXA` e `BB`.

- `Extractor`
  - Substituir `DataExtractor` por `BaseExtractor` com responsabilidades comuns: validação do PDF, abertura com `pdfplumber`, iteração por páginas/linhas e utilitários de normalização.
  - `CaixaExtractor`: extração stateless usando a regex configurada para `CAIXA`; produzir colunas brutas compatíveis com o schema comum.
  - `BBExtractor`: extração stateful.
  - Ao encontrar `padrao_linha_saldo`, atualizar `ano_atual` e `mes_anterior`.
  - Ao encontrar linha de movimento com data `DD.MM`, montar a data completa usando `ano_atual`.
  - Se a nova linha vier com mês `01` e `mes_anterior` estiver em `12`, incrementar `ano_atual` antes de compor a data.
  - Se o PDF não produzir linhas compatíveis suficientes com o banco escolhido, lançar erro de layout incompatível.
  - `ExtractorFactory.create(bank_name, bank_rules)` deve instanciar `CaixaExtractor` ou `BBExtractor`.

- `Transformer`
  - Alterar `apply_business_rules` para receber a configuração do banco, não só o mapa de rubricas.
  - Usar `bank_rules["formato_data"]` no parsing de datas.
  - Aplicar classificação com `bank_rules["rubricas"]`.
  - Padronizar saída comum com: `Data`, `Documento`, `Historico`, `Valor`, `Tipo_Valor`, `Saldo`, `Tipo_Saldo`, `Natureza_Operacao`, `Banco`, `Pagina`, `Linha`.
  - Para BB, preencher `Documento`, `Saldo` e `Tipo_Saldo` com `null` quando ausentes.

- `Pipeline / Interface`
  - `eel.start_etl_process(pdf_filename, bank_name)` passa a exigir os dois parâmetros.
  - `ETLPipeline.run_pipeline(pdf_path, bank_name)` deve:
  - carregar apenas as regras do banco escolhido;
  - criar o extrator via factory;
  - transformar com as regras do banco;
  - carregar em `Movimentacoes_CAIXA` ou `Movimentacoes_BB`.
  - Atualizar resultados e logs para incluir o banco processado e o nome final da tabela.
  - Atualizar frontend com `<select id="bank_selector">` e impedir processamento sem PDF e sem banco selecionado.
  - Atualizar o texto da UI para refletir “extrato bancário” com seleção de banco.
  - Atualizar `test_etl.py`, `main.py` e `backend/__init__.py` para as novas assinaturas/exportações.

## APIs e contratos públicos
- `RulesEngine.get_bank_rules(bank_name: str) -> dict`
- `ExtractorFactory.create(bank_name: str, bank_rules: dict) -> BaseExtractor`
- `extract_data(pdf_path: Path, bank_name: str) -> pd.DataFrame`
- `DataTransformer.apply_business_rules(df: pd.DataFrame, bank_rules: dict) -> pd.DataFrame`
- `ETLPipeline.run_pipeline(pdf_path: str, bank_name: str) -> dict`
- `eel.start_etl_process(pdf_filename: str, bank_name: str) -> dict`

## Testes
- Smoke test CAIXA com o PDF já existente.
- Teste unitário do `RulesEngine` validando JSON multi-banco e erro para banco inexistente.
- Teste unitário do `ExtractorFactory` para seleção correta do extrator.
- Teste unitário do `BBExtractor` com linhas sintéticas cobrindo:
  - leitura de `Saldo em DD.MM.YYYY`;
  - composição de data `DD.MM + ano_atual`;
  - virada de ano `12 -> 01`.
- Teste do transformer garantindo:
  - parsing de data por banco;
  - classificação por rubrica;
  - preenchimento de nulos no schema comum do BB.
- Teste do pipeline garantindo tabela `Movimentacoes_<BANCO>` e falha explícita quando o layout do PDF não combina com o banco selecionado.

## Premissas adotadas
- O arquivo de regras continua em [output/regras_extrato.json](/c:/Users/pedro.galvao/Documents/projetos_app_github/etl_app_depositos_judiciais/output/regras_extrato.json).
- O BB será persistido no mesmo schema lógico da CAIXA, com campos ausentes como `null`.
- Não haverá autodetecção de banco nesta iteração; a seleção do usuário é mandatória e validada.
- Como o repositório não mostra um PDF de amostra do BB, os testes do extrator BB serão baseados em texto sintético/mock de linhas extraídas.
