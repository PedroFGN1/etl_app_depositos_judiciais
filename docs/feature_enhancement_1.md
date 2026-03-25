# Melhoria de Feature: Tratamento de Saldo como Evento Independente (BBExtractor)

A implementação da arquitetura Multi-Banco foi um sucesso. No entanto, durante os testes com o Extrato do Banco do Brasil, identificamos que a linha de "Saldo em 30.01.2026 498.090.205,01 C" está sendo usada apenas como gatilho para atualizar a memória do ano, sendo descartada logo em seguida. 

Isso gera um problema de negócio: o saldo do último dia do mês anterior (ex: 30/01), que não possui movimentações, não está sendo salvo no banco de dados. 

Para resolver isso de forma elegante e manter o schema unificado (onde movimentações têm `Valor` preenchido e fechamentos têm `Saldo` preenchido), vamos transformar a linha de saldo do BB em um registro próprio.

Implemente as seguintes alterações no código:

### 1. Atualização do Motor de Regras (`regras_extrato.json` ou `rules_engine.py`)
- Altere a expressão regular `padrao_linha_saldo` do BB para capturar também o valor e o tipo (C/D). A nova Regex deve ser exatamente esta:
  `"^Saldo em (\\d{2}\\.\\d{2}\\.\\d{4})\\s+([\\d\\.,]+)\\s+([CD])"`
  *(Grupo 1 = Data, Grupo 2 = Valor do Saldo, Grupo 3 = Tipo do Saldo)*
- Adicione uma rubrica de controle nas regras do BB para classificar essa nova linha. Exemplo: 
  `"SALDO DIARIO": "Saldo Atualizado"`

### 2. Atualização no `BBExtractor` (`extractor.py`)
Dentro do loop de leitura de linhas da classe `BBExtractor`, quando a linha der *match* com `padrao_linha_saldo`:
- **Mantenha** a lógica atual que extrai a data (Grupo 1) e atualiza o `ano_atual` e `mes_anterior` na memória da classe.
- **Adicione** a extração do valor do saldo (Grupo 2) e do tipo (Grupo 3).
- **Gere um novo registro (yield/append)** e adicione à lista de extração, com a seguinte estrutura de dicionário bruto:
  - `Data`: A data capturada (Grupo 1)
  - `Documento`: `None`
  - `Historico`: `"SALDO DIARIO"` (Texto fixo para fazer match com o JSON)
  - `Valor`: `None`
  - `Tipo_Valor`: `None`
  - `Saldo`: O valor capturado (Grupo 2)
  - `Tipo_Saldo`: O tipo capturado (Grupo 3)

### Restrições e Cuidados
- **Não altere** a lógica do `CaixaExtractor`.
- **Não altere** o `transformer.py` (ele já deve ser capaz de lidar com colunas `Valor` nulas e `Saldo` preenchidas no processo de Data Cleaning graças ao schema unificado).
- Garanta que o pipeline continue ignorando linhas que não deem match nem com o saldo nem com a movimentação (apenas gerando `log_warning`).

Por favor, gere os trechos de código atualizados para o `BBExtractor` e para a inicialização/validação do `regras_extrato.json`.