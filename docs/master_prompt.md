# Contexto e Objetivo
Você atuará como um Engenheiro de Dados Sênior especialista em Python. O objetivo é refatorar um protótipo existente de uma aplicação ETL Desktop (construída em Python no backend e HTML/JS/Eel no frontend) para um novo cenário de uso.

O protótipo atual cruza tabelas CSV/Excel com regras de negócio fixas (hardcoded). A nova versão deverá extrair dados de extratos bancários em formato PDF (da Caixa Econômica Federal) e classificar as operações financeiras utilizando um motor de regras totalmente dinâmico, baseado em um arquivo JSON configurável pelo usuário.

# Regras Arquiteturais e de Segurança
1. **O que NÃO deve ser alterado:** Mantenha intacta a infraestrutura base. Não altere a lógica principal do `loader.py` (conexões de banco de dados), `logger.py` (sistema de logs), as configurações de banco no `config.py` e a estrutura visual do frontend (HTML/CSS).
2. **Gerenciamento de Estado Seguro:** Remova qualquer estado global persistente (ex: instâncias únicas globais de classes do pipeline). Cada clique em "Iniciar Processamento" na interface deve gerar uma nova instância do pipeline ETL para evitar *race conditions* ou contaminação de variáveis entre execuções.
3. **Tratamento de Erros:** Qualquer linha do PDF que não for reconhecida pela Expressão Regular não deve quebrar a aplicação; ela deve ser logada como *warning* (linha ignorada).
4. **Desempenho:** Como o Eel roda localmente, otimize o `eel_interface.py` para ler o PDF diretamente do disco do usuário ou gerenciar o base64 de forma eficiente, salvando em um diretório temporário antes de processar.

# Especificações por Módulo (Arquivos a serem reescritos/criados)

### 1. Novo Módulo: `rules_engine.py`
Crie esta nova classe (`RulesEngine`). 
* **Função:** Carregar, validar e fornecer um mapeamento "De/Para" a partir de um arquivo `regras_extrato.json`.
* **Exemplo de JSON esperado:** `{"DB TR CT": "Resgate", "CR J SELIC": "Rendimento", "TAR MANUT": "Tarifa"}`
* **Segurança:** Deve validar se o JSON está bem formatado e retornar um dicionário seguro para o sistema. Se o arquivo não existir, crie um JSON padrão com as regras acima.

### 2. Refatoração: `extractor.py`
Abandone a leitura de CSV/Excel. O foco agora é extração de PDF.
* **Ferramenta:** Utilize `pdfplumber` ou `PyPDF2`.
* **Lógica:** Itere sobre as páginas e extraia o texto linha a linha.
* **RegEx:** Crie uma Expressão Regular para capturar as linhas de movimentação financeira do extrato da Caixa. O padrão esperado no texto é: `[Data] [Documento] [Histórico] [Valor] [C/D] [Saldo] [C/D]`.
  * *Exemplo real da linha:* `27/02/2026 000000 DB TR CT 680,68 D 214.985.169,12 C`
* **Saída:** Um DataFrame bruto contendo as colunas capturadas pelo RegEx.

### 3. Refatoração: `transformer.py`
Remova as regras de negócio fixas (como `month_map` ou renomeação manual de colunas de processos judiciais).
* **Lógica Principal:** Crie um método `apply_business_rules(df, rules_dict)`. Ele deve receber o DataFrame bruto do extrator e o dicionário do `RulesEngine`.
* **Transformação:**
  1. Limpe os valores monetários (remova pontos e troque vírgulas por pontos, convertendo para float).
  2. Converta a string de data para formato ISO `YYYY-MM-DD`.
  3. **Classificação:** Compare a string da coluna "Histórico" capturada com as chaves do `rules_dict`. Preencha uma nova coluna chamada `Natureza_Operacao`. Se o histórico não estiver mapeado no JSON, classifique como "Desconhecido" e acione o `log_warning`.
* **Saída:** Um DataFrame limpo e tipado, pronto para o `loader.py`.

### 4. Ajustes: `etl_pipeline.py` e `eel_interface.py`
* No `etl_pipeline.py`, ajuste a orquestração para instanciar as novas classes e passar o motor de regras entre o `extractor` e o `transformer`.
* No `eel_interface.py`, certifique-se de que a função exportada ao frontend receba o nome do PDF e acione a nova orquestração, garantindo a limpeza do diretório temporário ao final.

# Saída Esperada
Gere o código completo, comentado e em Python, para os arquivos `rules_engine.py`, `extractor.py`, `transformer.py` e `etl_pipeline.py`, seguindo estritamente as assinaturas dos módulos de log originais (`log_info`, `log_error`, etc).