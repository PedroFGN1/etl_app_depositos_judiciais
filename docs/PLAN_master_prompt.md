# Refatoração do ETL para Extrato PDF com Regras Dinâmicas

## Resumo
Migrar o pipeline de um fluxo CSV/Excel de `saldos` + `resgates` para um fluxo de 1 PDF de extrato bancário da Caixa, com classificação dinâmica por JSON, preservando `loader.py`, `logger.py`, configurações de banco em `config.py` e a estrutura visual HTML/CSS. O processamento deve ser isolado por execução, sem reutilizar instâncias globais de pipeline/extrator/transformador entre cliques.

## Mudanças de Implementação
- Criar `backend/rules_engine.py` com uma classe `RulesEngine` que:
  - Resolva o caminho de `regras_extrato.json` em uma pasta estável do projeto, preferencialmente ao lado de `output` ou `uploads`, sem alterar a infraestrutura de config existente.
  - Crie automaticamente um JSON padrão se o arquivo não existir.
  - Valide leitura, tipo raiz `dict`, chaves/valores string não vazios e retorne um `dict[str, str]` seguro.
  - Faça log com `log_info`, `log_warning` e `log_error` sem mudar as assinaturas atuais do logger.

- Reescrever `backend/extractor.py` para PDF:
  - Substituir a lógica de CSV/Excel por uma classe `DataExtractor` focada em `.pdf`.
  - Validar existência, extensão e leitura do arquivo.
  - Usar `pdfplumber` como biblioteca principal de extração de texto.
  - Iterar por páginas, quebrar texto em linhas e aplicar uma regex tolerante ao padrão Caixa:
    - `data`, `documento`, `historico`, `valor`, `tipo_valor`, `saldo`, `tipo_saldo`
  - Ignorar linhas não reconhecidas com `log_warning`, sem interromper o fluxo.
  - Retornar um DataFrame bruto apenas com registros reconhecidos e colunas padronizadas.
  - Manter uma função de conveniência compatível com o novo cenário, agora recebendo um único `pdf_path`.

- Reescrever `backend/transformer.py` para o novo domínio:
  - Remover regras antigas de `month_map`, parsing de colunas mensais e modelagem de `saldos/resgates`.
  - Implementar `apply_business_rules(df, rules_dict)`.
  - Normalizar monetários brasileiros para `float`, datas para `YYYY-MM-DD` e padronizar tipos.
  - Criar `Natureza_Operacao` por correspondência do `Historico` com o JSON.
  - Usar correspondência exata após normalização básica do histórico; quando não houver regra, marcar `Desconhecido` e emitir `log_warning`.
  - Entregar um DataFrame final pronto para carga, com nomes de coluna estáveis e sem dependência de regras hardcoded.

- Ajustar `backend/etl_pipeline.py`:
  - Remover dependência das instâncias globais de extrator/transformador.
  - Fazer `ETLPipeline` instanciar `DataExtractor`, `RulesEngine` e `DataTransformer` no `__init__` de cada execução.
  - Trocar o fluxo para: validar PDF -> carregar regras -> extrair -> transformar -> carregar.
  - Carregar apenas 1 tabela final de movimentações classificadas via `loader.py`, sem alterar o loader.
  - Atualizar `results`, progresso e mensagens para refletirem 1 arquivo de entrada e 1 tabela de saída.
  - Manter uma função pública de entrada compatível com o novo contrato de 1 PDF.

- Ajustar `backend/eel_interface.py`:
  - Parar de reutilizar a instância global `etl_pipeline`; criar uma nova `ETLPipeline()` dentro de cada `start_etl_process`.
  - Alterar a função exposta para receber 1 nome de PDF.
  - Preservar a estrutura visual existente, mas adaptar a integração backend para o novo contrato.
  - Tratar upload de PDF com gravação em diretório temporário/seguro antes do processamento.
  - Garantir limpeza do temporário ao fim do processamento, inclusive em erro.
  - Manter logs, status e tratamento de exceções no mesmo padrão atual.

- Ajustes complementares necessários para o plano fechar:
  - Atualizar `frontend/app.js` para aceitar `.pdf`, operar com um único upload real e chamar `eel.start_etl_process(pdfName)`.
  - Manter `frontend/index.html` e `frontend/styles.css` estruturalmente intactos; apenas o comportamento JS muda.
  - Atualizar `requirements.txt` para incluir `pdfplumber`.

## Interfaces Públicas e Saídas
- `RulesEngine.load_rules() -> dict[str, str]`
- `DataExtractor.extract_file(pdf_path: Path) -> pandas.DataFrame`
- `DataTransformer.apply_business_rules(df: pandas.DataFrame, rules_dict: dict[str, str]) -> pandas.DataFrame`
- `ETLPipeline.run_pipeline(pdf_path: str) -> dict`
- `eel.start_etl_process(pdf_filename: str) -> dict`
- Tabela final carregada no banco:
  - Nome recomendado: reutilizar uma tabela única nova e explícita, como `Movimentacoes_Extrato`, definida localmente no pipeline sem mexer na configuração-base do banco.

## Testes e Cenários
- PDF válido com linhas reconhecidas gera DataFrame extraído e tabela carregada com sucesso.
- PDF com mistura de linhas válidas e inválidas não quebra; inválidas viram `warning`.
- Histórico presente no JSON classifica corretamente em `Natureza_Operacao`.
- Histórico ausente no JSON vira `Desconhecido` com `warning`.
- Arquivo `regras_extrato.json` inexistente é criado com o conteúdo padrão.
- JSON malformado falha com erro claro e log apropriado.
- Valores monetários como `214.985.169,12` viram `214985169.12`.
- Datas como `27/02/2026` viram `2026-02-27`.
- Cada chamada de `start_etl_process` cria um pipeline novo e não reaproveita estado anterior.
- Upload/processamento limpa arquivos temporários no sucesso e na exceção.
- Teste smoke do fluxo E2E via script deve ser atualizado para usar 1 PDF de amostra.

## Premissas e Defaults
- Seguir o caminho de 1 PDF real como entrada do produto.
- Carregar apenas 1 tabela final de movimentações classificadas.
- Usar `pdfplumber` como dependência padrão.
- Manter HTML/CSS sem refatoração estrutural; a adaptação de UX fica limitada ao JavaScript e aos textos já existentes quando estritamente necessário.
- Preservar `loader.py`, `logger.py` e `config.py` sem mudanças funcionais, exceto eventual consumo de nomes de tabela a partir do pipeline.
