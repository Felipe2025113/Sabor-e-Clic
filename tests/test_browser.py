"""Fluxo real HTTP/Chrome. Requer a mesma base descartável do test_mysql.py."""
import os
from pathlib import Path
from threading import Thread
import pytest
from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server
from test_mysql import db


@pytest.fixture
def servidor(db):
    server = make_server('127.0.0.1', 0, db, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()
    thread.join()


def entrar(pagina, base, email, senha, destino):
    pagina.goto(base+'/templates/CadastroCliente.html')
    pagina.locator('#login-email').fill(email)
    pagina.locator('#login-senha').fill(senha)
    pagina.locator('#form-login button[type=submit]').click()
    pagina.wait_for_url('**/'+destino)


def test_fluxo_visual_completo(servidor):
    destino = Path(os.getenv('EVIDENCIAS_DIR','docs/evidencias'))
    destino.mkdir(parents=True, exist_ok=True)
    erros, falhas = [], []
    with sync_playwright() as p:
        opcoes = {'headless':True}
        if os.getenv('CHROME_EXECUTABLE'):
            opcoes['executable_path'] = os.environ['CHROME_EXECUTABLE']
        browser = p.chromium.launch(**opcoes)
        def nova_pagina():
            context = browser.new_context(viewport={'width':1366,'height':900})
            page = context.new_page()
            page.on('pageerror', lambda e: erros.append(str(e)))
            page.on('requestfailed', lambda r: falhas.append(r.url))
            page.on('response', lambda r: falhas.append(f'{r.status} {r.url}') if r.status >= 400 and not (r.status == 401 and r.url.endswith('/api/me')) else None)
            return page
        cliente, admin, chef = nova_pagina(), nova_pagina(), nova_pagina()
        cliente.goto(servidor+'/')
        expect(cliente.locator('h1')).to_contain_text('Sabor & Clic')
        cliente.screenshot(path=str(destino/'inicio-desktop.png'),full_page=True)
        chef.goto(servidor+'/templates/CadastroCozinheiro.html')
        chef.locator('[data-ir="cadastro-cozinheiro"]:visible').click()
        chef.locator('#coz-nome').fill('Chef Navegador')
        chef.locator('#coz-email').fill('chef.browser@example.com')
        chef.locator('#coz-turno').select_option(label='Noite')
        chef.locator('#coz-especialidade').select_option(label='Massas e molhos')
        chef.locator('#form-cadastro-cozinheiro button[type=submit]').click()
        expect(chef.locator('#mensagem')).to_contain_text('Cadastro enviado')
        entrar(admin,servidor,'carlos@email.com','TesteSeguro123','ADM.html')
        expect(admin.locator('#lista-admin-pratos .item-cardapio')).to_have_count(3)
        linha = admin.locator('.linha-solicitacao').filter(has_text='Chef Navegador')
        linha.get_by_role('button',name='Aprovar',exact=True).click()
        provisoria = admin.locator('#aviso-senha strong').inner_text()
        admin.locator('#aviso-senha').get_by_role('button',name='Fechar',exact=True).click()
        entrar(chef,servidor,'chef.browser@example.com',provisoria,'Cozinheiro.html')
        expect(chef.locator('[data-tela="troca-senha"]')).to_be_visible()
        chef.locator('#senha-atual').fill(provisoria)
        chef.locator('#senha-nova').fill('Definitiva123')
        chef.locator('#senha-confirmacao').fill('Definitiva123')
        chef.locator('#form-troca-senha button[type=submit]').click()
        expect(chef.locator('[data-tela="cozinha"]')).to_be_visible()
        cliente.goto(servidor+'/templates/CadastroCliente.html')
        cliente.locator('[data-ir="cadastro-cliente"]:visible').click()
        cliente.locator('#cli-nome').fill('Cliente Navegador')
        cliente.locator('#cli-email').fill('cliente.browser@example.com')
        cliente.locator('#cli-endereco').fill('Rua Navegador 123')
        cliente.locator('#cli-senha').fill('ClienteSeguro123')
        cliente.locator('#form-cadastro-cliente button[type=submit]').click()
        expect(cliente.locator('#mensagem')).to_contain_text('Cadastro realizado')
        cliente.locator('#login-email').fill('cliente.browser@example.com')
        cliente.locator('#login-senha').fill('ClienteSeguro123')
        cliente.locator('#form-login button[type=submit]').click()
        cliente.wait_for_url('**/Cliente.html')
        expect(cliente.locator('#lista-cardapio .item-cardapio')).to_have_count(3)
        cliente.locator('#lista-cardapio [data-acao="adicionar"]').first.click()
        expect(cliente.locator('#total-carrinho')).to_contain_text('25,00')
        cliente.locator('#btn-finalizar').click()
        expect(cliente.locator('#mensagem')).to_contain_text('realizado com sucesso')
        expect(cliente.locator('#kds-col-aguardando .kds-cartao')).to_have_count(1)
        cliente.screenshot(path=str(destino/'cliente-desktop.png'),full_page=True)
        # A fila e o acompanhamento se atualizam automaticamente, sem recarregar a página.
        cartao = chef.locator('.linha-pedido-cozinha').filter(has_text='Cliente Navegador')
        expect(cartao).to_be_visible(timeout=10000)
        cartao.locator('input').fill('15')
        cartao.get_by_role('button',name='Iniciar Preparo').click()
        expect(cartao.get_by_role('button',name='Marcar como Pronto')).to_be_visible()
        chef.screenshot(path=str(destino/'cozinha-desktop.png'),full_page=True)
        cartao.get_by_role('button',name='Marcar como Pronto').click()
        expect(cartao.get_by_role('button',name='Marcar como Entregue')).to_be_visible()
        cartao.get_by_role('button',name='Marcar como Entregue').click()
        expect(cliente.locator('#kds-col-entregue .kds-cartao')).to_have_count(1,timeout=10000)
        # Formulário do administrador e catálogo CRUD, preservando o HTML.
        admin.locator('#adm-nome').fill('Administrador Navegador')
        admin.locator('#adm-email').fill('admin.browser@example.com')
        admin.locator('#adm-senha-atual').fill('TesteSeguro123')
        admin.locator('#form-dados-adm button[type=submit]').click()
        expect(admin.locator('#mensagem')).to_contain_text('Dados atualizados')
        admin.locator('#prato-nome').fill('<img src=x onerror=alert(1)>')
        admin.locator('#prato-descricao').fill('Prato de teste do navegador')
        admin.locator('#prato-preco').fill('12.50')
        admin.locator('#prato-categoria').fill('Testes')
        admin.locator('#form-prato button[type=submit]').click()
        expect(admin.locator('#mensagem')).to_contain_text('Prato salvo')
        novo = admin.locator('#lista-admin-pratos .item-cardapio').filter(has_text='<img src=x')
        expect(novo.locator('img')).to_have_count(0)
        novo.get_by_role('button',name='Editar',exact=True).click()
        admin.locator('#prato-nome').fill('Prato Navegador')
        admin.locator('#form-prato button[type=submit]').click()
        novo = admin.locator('#lista-admin-pratos .item-cardapio').filter(has_text='Prato Navegador')
        expect(novo).to_be_visible()
        novo.get_by_role('button',name='Inativar',exact=True).click()
        expect(novo.get_by_role('button',name='Ativar',exact=True)).to_be_visible()
        admin.on('dialog',lambda dialog: dialog.accept())
        novo.get_by_role('button',name='Remover',exact=True).click()
        expect(novo).to_have_count(0)
        admin.screenshot(path=str(destino/'admin-desktop.png'),full_page=True)
        for nome, pagina in [('cliente',cliente),('admin',admin),('cozinha',chef)]:
            pagina.set_viewport_size({'width':390,'height':844})
            pagina.screenshot(path=str(destino/f'{nome}-mobile.png'),full_page=True)
            assert pagina.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), nome
        # Saída e proteção após encerrar sessão.
        cliente.locator('[data-logout]').click()
        cliente.wait_for_url('**/CadastroCliente.html')
        cliente.goto(servidor+'/templates/Cliente.html')
        cliente.wait_for_url('**/CadastroCliente.html')
        assert not erros, erros
        assert not falhas, falhas
        browser.close()
