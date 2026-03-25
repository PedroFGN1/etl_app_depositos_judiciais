Você atuará como um Engenheiro de Dados Sênior especialista em Python. Precisamos fazer uma melhoria na última implementação feita. A ferramenta não lerá apenas os extratos da CAIXA, mas também os do Banco do Brasil (BB). 

O desafio é que os extratos possuem layouts e rubricas totalmente diferentes, e o BB omite o ano nas linhas de transação (ex: "27.02"). Para garantir a escalabilidade e evitar código "espaguete", atualize e implemente o código seguindo estas novas diretrizes de Arquitetura Multi-Banco:

# 1. Atualização no Motor de Regras (`regras_extrato.json`)
O JSON agora deve ser estruturado por banco. Além do "De/Para" das rubricas, ele deve ditar as Expressões Regulares (Regex) e o formato da data. Isso permite adaptar o sistema sem mexer no código Python.
Exemplo estrutural esperado:
```json
{
  "CAIXA": {
    "padrao_linha_movimento": "^(\\d{2}/\\d{2}/\\d{4})\\s+(\\d+)\\s+(.+?)\\s+([\\d\\.,]+)\\s+([CD])",
    "formato_data": "%d/%m/%Y",
    "rubricas": { "DB TR CT": "Resgate", "CR J SELIC": "Rendimento" }
  },
  "BB": {
    "padrao_linha_saldo": "^Saldo em (\\d{2}\\.\\d{2}\\.\\d{4})",
    "padrao_linha_movimento": "^(\\d{2}\\.\\d{2})\\s+(\\d+)?\\s+(.+?)\\s+([\\d\\.,]+)\\s+([CD])",
    "formato_data": "%d.%m.%Y",
    "rubricas": { "ANOTAÇÃO DE RESGATE EM FUNDO GARANT": "Resgate", "ATUALIZACAO DE REC APLICADOS": "Rendimento" }
  }
}
```
# 2. Implementação do Padrão Strategy/Factory (extractor.py)
- Crie uma classe abstrata/mãe `BaseExtractor` que gerencia a abertura do PDF via `pdfplumber`.

- Crie `CaixaExtractor(BaseExtractor)`: Faz a extração "stateless" (linha a linha isolada) usando a Regex da CAIXA mapeada no JSON.

- Crie `BBExtractor(BaseExtractor)`: Faz extração "stateful" (com memória).
  - A Regra da Virada de Ano: O extrator deve identificar a linha de "Saldo em DD.MM.YYYY" com Regex, guardar o `ano_atual` e o `mes_anterior` na memória da classe. Nas linhas seguintes (que têm apenas "DD.MM"), ele concatena com o ano da memória. Atenção: Se o mês da linha lida for "01" e o `mes_anterior` na memória for "12", ele deve somar +1 ao `ano_atual` armazenado antes de concatenar, resolvendo a transição de ano.

- Crie um `ExtractorFactory` que instancie a classe correta com base no nome do banco selecionado.

# 3. Ajustes na Interface e Pipeline (eel_interface.py, app.js e HTML)
- No Frontend (HTML/JS), adicione um simples `<select id="bank_selector">` com as opções "CAIXA" e "BB".

- A função `eel.start_etl_process` passará a receber dois parâmetros: `pdf_filename` e `bank_name`.

- O `etl_pipeline.py` utilizará o `bank_name` para instanciar o extrator correto via Factory e passar apenas as regras daquele banco para o `transformer.py`.

- Loader: O pipeline deve instruir o `loader.py` a salvar os dados em tabelas separadas (ex: `Movimentacoes_CAIXA` ou `Movimentacoes_BB`), para não quebrar a integridade com layouts misturados.

Pode confirmar o entendimento destas adições e começar a gerar os códigos dos módulos atualizados (Rules Engine, Extractor, Transformer e Pipeline).