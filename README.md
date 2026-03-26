# Sistema ETL - Extratos Bancários de Depósitos Judiciais

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-orange.svg)

Esta é uma aplicação de **Engenharia de Dados** voltada para o processamento de extratos bancários de depósitos judiciais em formato PDF. O sistema foi projetado para atender ao rigor necessário em auditorias financeiras governamentais (Estado de GO vs. Bancos Públicos), garantindo a precisão "centavo por centavo".

O ecossistema realiza a extração, transformação e carga (ETL) de dados brutos inconsistentes, convertendo-os em esquemas estruturados e unificados para análise e auditoria.

## 📋 Visão Geral

O projeto resolve o desafio de consolidar fontes de dados distintas (Caixa Econômica Federal e Banco do Brasil) que possuem layouts de extratos frequentemente mal formatados e sem metadados padronizados.

### Principais Diferenciais:
- **Resiliência de Dados:** Tratamento robusto para PDFs/CSVs com inconsistências estruturais.
- **Rigor Matemático:** Lógica de processamento focada na integridade absoluta dos valores para fins de auditoria.
- **Arquitetura Modular:** Separação clara entre extração, regras de negócio e persistência.
- **Interface Amigável:** Operação simplificada via interface web (Eel) com feedback em tempo real.

---

## 🚀 Funcionalidades

- **Interface Web:** Interface intuitiva desenvolvida com Eel.
- **Upload Inteligente:** Suporte a *drag-and-drop* para arquivos PDF.
- **Pipeline ETL Modular:** Fluxo desacoplado em `extract`, `transform` e `load`.
- **Motor de Regras (Rules Engine):** Regras de classificação e extração configuráveis via JSON.
- **Multi-Banco:** Suporte nativo para SQLite, PostgreSQL, MySQL e SQL Server.
- **Observabilidade:** Logs detalhados em tempo real com níveis de severidade e opção de exportação.
- **Garantia de Qualidade:** Suíte de testes automatizados para validadores, extratores e transformadores.

---

## 📂 Estrutura do Projeto

```text
etl_app_depositos_judiciais/
├── backend/                # Núcleo de processamento e lógica de negócio
│   ├── extractor.py        # Extratores específicos (Caixa e BB)
│   ├── transformer.py      # Padronização de esquemas e tipos de dados
│   ├── rules_engine.py     # Motor de classificação baseado em rubricas
│   ├── loader.py           # Interface de persistência em banco de dados
│   └── etl_pipeline.py     # Orquestrador do fluxo ETL
├── frontend/               # Interface web (HTML/CSS/JS)
├── data_samples/           # Amostras de dados para teste e validação
├── docs/                   # Documentação técnica e planos de melhoria
├── main.py                 # Ponto de entrada da aplicação
├── requirements.txt        # Dependências do sistema
└── test_etl.py             # Testes unitários e de integração
```

---

## 🛠️ Arquitetura e Fluxo de Dados

O sistema opera sob um fluxo de processamento dirigido por regras:

1. **Entrada:** O usuário seleciona a instituição financeira e realiza o upload do PDF.
2. **Extração:** O `ExtractorFactory` identifica o extrator adequado (`CaixaExtractor` ou `BBExtractor`).
   - *Nota:* O extrator do BB é *stateful*, gerenciando a persistência de ano em datas curtas (`DD.MM`).
3. **Transformação:** O `DataTransformer` aplica o esquema unificado, tratando tipagem e normalização de valores.
4. **Carga:** O `DataLoader` persiste os dados nas tabelas correspondentes (`Movimentacoes_CAIXA` ou `Movimentacoes_BB`).

### Esquema de Saída Unificado
| Campo | Descrição |
| :--- | :--- |
| `Data` | Data da operação (formato ISO) |
| `Documento` | Número do documento/autenticação |
| `Historico` | Descrição da transação ou rubrica |
| `Valor` | Valor nominal da movimentação |
| `Tipo_Valor` | C (Crédito) ou D (Débito) |
| `Saldo` | Saldo remanescente após a operação |
| `Natureza_Operacao` | Classificação auditável da transação |

---

## 🔧 Instalação e Uso

### Pré-requisitos
- Python 3.10 ou superior.
- Navegador moderno (Chrome/Edge recomendado para Eel).

### Passo a Passo

1. **Clonar o repositório:**
   ```bash
   git clone https://github.com/PedroFGN1/etl_app_depositos_judiciais.git
   cd etl_app_depositos_judiciais
   ```

2. **Configurar o ambiente virtual:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # ou
   .\venv\Scripts\Activate.ps1 # Windows
   ```

3. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Executar a aplicação:**
   ```bash
   python main.py
   ```

---

## 🧪 Testes

Para garantir a integridade do processamento, execute a suíte de testes:

```bash
python -m unittest -v test_etl.py
```

A cobertura inclui validação de virada de ano (BB), processamento de rubricas especiais, consistência do schema unificado e testes de falha controlada para layouts incompatíveis.

---

## ⚖️ Licença

Este projeto está licenciado sob a licença MIT - consulte o arquivo [LICENSE](LICENSE) para detalhes.

---
> **Atenção:** Este software foi desenvolvido para suporte à auditoria financeira. Sempre valide os resultados finais com os documentos originais antes de tomar decisões governamentais ou jurídicas.
