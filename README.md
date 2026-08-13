# Framework de Auditoria de Segurança e Reconhecimento DevSecOps

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Uma ferramenta automatizada e modular de reconhecimento e auditoria de segurança, projetada para pipelines DevSecOps, avaliação de vulnerabilidades e testes de intrusão (pentest) web autorizados.

---

## 🚀 Principais Recursos

* **WAF Detection:** Identifica automaticamente Web Application Firewalls comuns (Cloudflare, AWS CloudFront, Akamai, ModSecurity, etc.) antes do envio de payloads.
* **Hyper-OSINT Engine:** Extrai e-mails ocultos, números de telefone, tokens de API (Google, Stripe, GitHub, AWS, JWT), hashes criptográficos e comentários de código-fonte das aplicações alvo.
* **Asynchronous Path Enumeration & WAF Bypassing:** Utiliza pooling com `gevent` para escanear rapidamente arquivos sensíveis críticos (`.env`, `wp-config.php`, backups, exposição de código-fonte) e testar vetores de bypass de WAF.
* **High-Performance Port Scanner:** Capacidade de escaneamento de portas assíncrono (estilo TCP SYN) para mapear rapidamente serviços de infraestrutura expostos.
* **Controlled Credential Brute-Forcing:** Descobre painéis administrativos e realiza validação direcionada utilizando wordlists dinâmicas, filtrando falsos positivos.
* **Comprehensive Reporting:** Compila automaticamente todas as descobertas em um arquivo estruturado `relatorio_auditoria.json` (para integração com pipelines CI/CD) e em um dashboard interativo moderno e limpo (`relatorio_auditoria.html`).

---

## 🛠️ Pré-requisitos e Instalação

Certifique-se de ter o Python 3.8+ instalado. Clone o repositório e instale as dependências necessárias:

```bash
git clone https://github.com/Mdsoare/devsecops-security-scanner.git
cd devsecops-security-scanner
pip install -r requirements.txt
```

### Dependências

- requests
- beautifulsoup4
- colorama
- gevent
- dnspython

---

## 📖 Guia de Uso

### 1.  Visão Geral das Funcionalidades e Exemplos

O framework executa uma auditoria modular sequencial: desde a detecção defensiva até a varredura de infraestrutura e exportação de relatórios.

#### A. Execução BásicaPara iniciar a ferramenta, execute o script em seu terminal e informe a URL ou o domínio do alvo desejado:

```bash
python devsecops_scanner.py
```
Quando solicitado, insira o domínio ou a URL de destino:

```text
Enter target (URL or domain): exemplo.com
```

---

#### B. Funcionalidades Detalhadas

1. Detecção Prévia de WAF (`detect_waf`)

- O que faz: Analisa os cabeçalhos HTTP e cookies de resposta (`Server`, `Set-Cookie`, etc.) para identificar a presença de firewalls de aplicação web conhecidos (como Cloudflare, AWS CloudFront, Akamai, ModSecurity).

Exemplo de Saída no Terminal:

```text
🛡️ DETECTANDO A PRESENÇA DE WAF NO ALVO...
🎯 WAF Identificado: Cloudflare WAF
```

---

2. OSINT e Coleta de Inteligência (`hyper_osint`)

- O que faz: Extrai e-mails, números de telefone, chaves de API corporativas/públicas, hashes criptográficos e comentários embutidos no código-fonte da página principal, além de realizar uma busca ativa em subdomínios comuns (`admin`, `dev`, `api`, `vpn`).

- Exemplo de Arquivos Gerados:

1. `api_keys_found.txt` (Caso chaves sensíveis sejam encontradas no escopo).
2. `hashes_found.txt` (Hashes extraídos do alvo).

- Exemplo de saída no terminal:

```text
💀 [HYPER-OSINT] TORCHING http://exemplo.com WITH EXTREME PREJUDICE
🎯 OSINT Concluído com sucesso.
```

- Exemplo de Análise e Exportação em Formato JSON:

1. Após a varredura completa, o dicionário global consolidado é gravado no arquivo `relatorio_auditoria.json`.
2. Estrutura interna salva no JSON:

```json
{
    "target": "http://exemplo.com",
    "waf_detected": "Cloudflare WAF",
    "vulnerabilities": [
        {
            "url": "http://exemplo.com/.env",
            "description": "CRITICO - .env exposto com senhas!"
        }
    ]
}
```

- Exemplo de Verificação de Relatório Visual:

1. O arquivo `relatorio_auditoria.html` gerado automaticamente agrupa as informações de segurança em blocos de cartões estilizados para facilitar a leitura em qualquer navegador web moderno.  

---

3. Teste de WAF Bypass Assíncrono (`waf_bypass_payloads`)

- O que faz: Dispara payloads codificados (como injeções SQL simuladas, path traversal e parameter pollution) de forma assíncrona utilizando `gevent` para verificar se o mecanismo de defesa bloqueia ou deixa passar as requisições.

---

4. Varredura de Portas de Alta Performance (`port_scan`)

- O que faz: Conecta-se às portas TCP do host de forma concorrente para mapear serviços ativos rapidamente.

- Exemplo de Saída no Terminal:

```text
💣 [SUPER BRUTAL PORT SCAN] ON exemplo.com — 1000 PORTS — 500 THREADS
🔓 OPEN PORT: 80/tcp → HTTP
🔓 OPEN PORT: 443/tcp → HTTPS
```
---

5. Enumeração de Diretórios e Força Bruta de Credenciais (`enumerar_vulnerabilidades` & `bruteforce_com_usuarios`)

- O que faz: Varre caminhos críticos e sensíveis (`/.env`, `/wp-config.php`, backups). Caso descubra usuários por meio da API REST (ex: WordPress), inicializa uma rotina de força bruta controlada validando sessões para mitigar falsos positivos.

- Exemplo de Saída de Arquivo (`possiveis_credenciais.txt`):

```text
VALIDADO - Painel: http://exemplo.com/wp-login.php | User: admin | Pass: admin123
```

---

### Artefatos Gerados

Após a conclusão, o framework gera os seguintes arquivos no diretório de trabalho:

1. `relatorio_auditoria.json`: Registro completo de auditoria técnica estruturado para leitura por máquinas.
2. `relatorio_auditoria.html`: Painel visual resumindo dados de OSINT, portas abertas descobertas e vulnerabilidades.
3. `api_keys_found.txt / hashes_found.txt`: Artefatos extraídos (caso algum seja identificado).
4. `possiveis_credenciais.txt`: Registro de tentativas de autenticação validadas.

---

## ⚙️ Configuração

Você pode configurar a rotação de proxies ou o roteamento local via Tor editando a lista `PROXIES` dentro do script:

```python
PROXIES = [
    # "http://user:pass@ip:port",
    # "socks5://127.0.0.1:9050" # Exemplo de proxy Tor local
]
```

---

## ⚠️ Aviso Legal

Esta ferramenta destina-se estritamente a auditorias de segurança autorizadas, fins educacionais e validação defensiva de DevSecOps. Não realize varreduras em sistemas sem permissão explícita e por escrito dos proprietários dos sistemas. Os autores não assumem responsabilidade pelo uso indevido.

---

## 📄 Licença
Distribuído sob a Licença MIT. Consulte o arquivo LICENSE para mais informações.

---

*Desenvolvido por **Marcelo Soares** | Especialista em Segurança da Informação e Computação Forense.*