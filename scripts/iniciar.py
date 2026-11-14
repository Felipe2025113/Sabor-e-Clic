"""Inicia a demonstração local usando o Docker e o Compose instalados."""
import argparse
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener
import webbrowser

PASTA = Path(__file__).resolve().parents[1]
CONFIG = PASTA / '.sabor.env'
ADMIN_CRIADO = PASTA / '.sabor-admin-criado'
EMAIL_ADMIN = 'admin@saborclic.local'


def docker_disponivel(comando, ambiente):
    return subprocess.run(comando, env=ambiente, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0


def preparar_docker():
    if not shutil.which('docker'):
        raise RuntimeError('O iniciador precisa do Docker com Compose instalado.')
    ambiente = os.environ.copy()
    if not docker_disponivel(['docker', 'info'], ambiente):
        if sys.platform == 'darwin' and shutil.which('colima'):
            subprocess.run(['colima', 'start', '--activate=false'], check=True)
            ambiente.pop('DOCKER_HOST', None)
            ambiente['DOCKER_CONTEXT'] = 'colima'
        else:
            raise RuntimeError('Abra o Docker Desktop e execute este iniciador novamente.')
    if docker_disponivel(['docker', 'compose', 'version'], ambiente):
        return ['docker', 'compose'], ambiente
    if shutil.which('docker-compose'):
        return ['docker-compose'], ambiente
    raise RuntimeError('O Docker Compose não foi encontrado.')


def dados_instalacao():
    if not CONFIG.exists():
        dados = {
            'COMPOSE_PROJECT_NAME': f'sabor-clic-{secrets.token_hex(4)}',
            'MYSQL_PASSWORD': secrets.token_hex(24),
            'MYSQL_ROOT_PASSWORD': secrets.token_hex(24),
            'SECRET_KEY': secrets.token_hex(32),
            'SABOR_ADMIN_SENHA': secrets.token_hex(10) + 'A1',
        }
        descritor = os.open(CONFIG, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descritor, 'w', encoding='utf-8') as arquivo:
            for chave, valor in dados.items():
                arquivo.write(f'{chave}={valor}\n')
    return dict(linha.split('=', 1) for linha in CONFIG.read_text(encoding='utf-8').splitlines())


def esperar_site(endereco):
    cliente = build_opener(ProxyHandler({}))
    limite = time.monotonic() + 30
    while time.monotonic() < limite:
        try:
            with cliente.open(endereco + 'api/health', timeout=3):
                return
        except (URLError, TimeoutError):
            time.sleep(1)
    raise RuntimeError(f'O navegador não conseguiu acessar o Flask e o MySQL em {endereco}.')


def main():
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument('--parar', action='store_true', help='Parar o site e o MySQL desta pasta.')
    opcoes = argumentos.parse_args()
    if opcoes.parar and not CONFIG.exists():
        print('Nenhum serviço foi iniciado por esta pasta.')
        return

    comando_compose, ambiente = preparar_docker()
    dados = dados_instalacao()
    ambiente.update(dados)
    # Publica uma porta livre, inclusive se outra cópia do projeto estiver aberta.
    ambiente['SABOR_PORTA'] = ''
    comando_compose += ['--env-file', str(CONFIG), '-p', dados['COMPOSE_PROJECT_NAME'],
                        '-f', str(PASTA / 'compose.yaml')]

    def executar(comando, **kwargs):
        return subprocess.run(comando, env=ambiente, cwd=PASTA, check=True, text=True, **kwargs)

    if opcoes.parar:
        executar(comando_compose + ['stop'])
        return

    print('Preparando o MySQL e o Sabor & Clic. A primeira abertura pode demorar.', flush=True)
    executar(['docker', 'build', '-t', 'sabor-clic-mysql:parte2', '-f', 'database/Dockerfile', '.'])
    executar(['docker', 'build', '-t', 'sabor-clic-web:parte2', '.'])
    executar(comando_compose + ['up', '-d', '--no-build', '--wait', '--wait-timeout', '150'])
    if not ADMIN_CRIADO.exists():
        entradas = f"Administrador Local\n{EMAIL_ADMIN}\n{dados['SABOR_ADMIN_SENHA']}\n"
        executar(comando_compose + ['exec', '-T', 'web', 'python', '-m', 'scripts.criar_admin', '--stdin'],
                 input=entradas)
        ADMIN_CRIADO.touch()

    porta = executar(comando_compose + ['port', 'web', '5000'], capture_output=True).stdout.strip()
    endereco = f'http://127.0.0.1:{int(porta.rsplit(":", 1)[1])}/'
    esperar_site(endereco)
    print(f'\nSabor & Clic pronto: {endereco}', flush=True)
    print('Acesso inicial de administrador pela área do cliente:')
    print(f"E-mail: {EMAIL_ADMIN}\nSenha inicial: {dados['SABOR_ADMIN_SENHA']}", flush=True)
    webbrowser.open(endereco)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as erro:
        sys.exit(f'Não foi possível iniciar o Sabor & Clic. {erro}')
