# Saldo BB como Evento Independente

## Resumo
Implementar no fluxo do BB o tratamento de cada linha `Saldo em ...` como um registro próprio do extrato, em vez de usá-la apenas como âncora de ano/mês. O schema unificado permanece igual: linhas de saldo terão `Saldo`/`Tipo_Saldo` preenchidos e `Valor`/`Tipo_Valor` nulos.
A classificação padrão do novo evento será `SALDO DIARIO -> Saldo Atualizado`.

## Mudanças de implementação
- `RulesEngine` / `regras_extrato`
  - Atualizar a regra default do BB em [backend/rules_engine.py](/c:/Users/pedro.galvao/Documents/projetos_app_github/etl_app_depositos_judiciais/backend/rules_engine.py) para usar exatamente:
    - `padrao_linha_saldo = "^Saldo em (\\d{2}\\.\\d{2}\\.\\d{4})\\s+([\\d\\.,]+)\\s+([CD])"`
  - Incluir nas rubricas default do BB:
    - `"SALDO DIARIO": "Saldo Atualizado"`
  - Manter a validação atual, apenas garantindo que o BB continue exigindo `padrao_linha_saldo` textual.
  - Atualizar também o arquivo runtime [output/regras_extrato.json](/c:/Users/pedro.galvao/Documents/projetos_app_github/etl_app_depositos_judiciais/output/regras_extrato.json) para manter o ambiente alinhado com o default.

- `BBExtractor`
  - Em [backend/extractor.py](/c:/Users/pedro.galvao/Documents/projetos_app_github/etl_app_depositos_judiciais/backend/extractor.py), quando `padrao_linha_saldo` casar:
    - capturar `data`, `saldo` e `tipo_saldo`;
    - continuar atualizando `current_year` e `previous_month` com a data;
    - retornar um registro bruto, não `None`, com:
      - `data = grupo 1`
      - `documento = None`
      - `historico = "SALDO DIARIO"`
      - `valor = None`
      - `tipo_valor = None`
      - `saldo = grupo 2`
      - `tipo_saldo = grupo 3`
      - `banco`, `pagina`, `linha` preenchidos pelo `create_base_row`
  - Manter intacta a lógica do `CaixaExtractor`.
  - Manter intacta a regra de virada de ano para linhas de movimento do BB.
  - Para linhas BB que não casarem nem com saldo nem com movimento, registrar `log_warning` com página, linha e conteúdo, e seguir ignorando a linha.

## Interfaces e comportamento
- Nenhuma assinatura pública precisa mudar.
- O contrato implícito do BB passa a ser:
  - `padrao_linha_saldo` com 3 grupos obrigatórios: data, valor do saldo, tipo do saldo.
  - `BBExtractor.process_line(...)` pode retornar registros tanto para linhas de movimento quanto para linhas de saldo.
- `transformer.py` não deve ser alterado; ele continuará recebendo o raw schema já compatível.

## Testes
- Atualizar os testes do BB em [test_etl.py](/c:/Users/pedro.galvao/Documents/projetos_app_github/etl_app_depositos_judiciais/test_etl.py):
  - adaptar o fixture de saldo para o novo formato, por exemplo `Saldo em 31.12.2025 1.234,56 C`;
  - validar que a extração do BB agora retorna também a linha de saldo como registro;
  - validar que o primeiro registro de saldo sai com `historico = "SALDO DIARIO"`, `valor = None`, `saldo = "1.234,56"`, `tipo_saldo = "C"`;
  - manter a verificação de virada de ano nas movimentações seguintes.
- Adicionar teste de transformação para confirmar que `SALDO DIARIO` é classificado como `Saldo Atualizado` e que `Valor` permanece nulo enquanto `Saldo` é convertido corretamente.
- Rodar o smoke test atual da CAIXA para garantir que nada mudou no outro extrator.

## Premissas
- Todas as linhas `Saldo em ...` do BB devem virar registro próprio, não apenas o saldo inicial do período.
- O rótulo de classificação adotado será `Saldo Atualizado`.
- O warning para linhas ignoradas será aplicado ao fluxo BB desta melhoria, já que esse requisito está explícito no arquivo e hoje não está refletido no comportamento atual.
