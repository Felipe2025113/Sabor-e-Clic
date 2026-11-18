# Execução e estrutura do projeto

Projeto da Parte 2 do IFSP. As telas originais são servidas pelo Flask, a API responde às chamadas do JavaScript e os dados são gravados no MySQL.

## Abrir o projeto

1. Extraia o ZIP em uma pasta. Tenha o Python 3.10+ e o Docker com Compose disponíveis. No Windows, abra o Docker Desktop.
2. Dê dois cliques em `Iniciar.bat` no Windows ou em `Iniciar.command` no macOS. No terminal, o mesmo iniciador é `python -m scripts.iniciar` (ou `python3`).
3. Aguarde o banco e o site ficarem prontos. O iniciador abre a URL local no navegador e mostra o acesso inicial de administrador. Para entrar como administrador, selecione a área do cliente na página inicial.

A primeira abertura pode baixar as imagens do Docker. O iniciador prepara o banco e as nove triggers. Os dados e a senha inicial da instalação são reutilizados ao abrir o projeto novamente pela mesma pasta. Guarde o arquivo local oculto `.sabor.env` para reabrir a mesma base. O código do GitHub vem sem senhas.

Use o endereço mostrado no terminal. Ele é a origem da página, dos arquivos estáticos e da API. O MySQL usa o endereço interno `db:3306` na rede do Docker. Para desligar os serviços desta pasta, execute `python -m scripts.iniciar --parar`.

## Executar o Docker Compose manualmente

Copie `.env.example` para `.env` e preencha `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` e `SECRET_KEY` com valores próprios. Em seguida, execute:

```sh
docker compose up -d --build --wait
docker compose exec web python -m scripts.criar_admin
```

Abra **http://127.0.0.1:5055/**. Se a porta já estiver em uso, ajuste `SABOR_PORTA` no `.env` e abra a nova porta. Para parar mantendo os cadastros e pedidos, execute `docker compose down`. Os dados iniciais têm hashes fictícios. O script de administrador e o formulário de cadastro criam contas com senhas válidas.

## Alternativa: Python e MySQL instalados

Requer Python 3.10 ou superior e MySQL 8.4 (InnoDB).

```sh
python -m venv .venv
```

Ative o ambiente: Windows PowerShell: `.venv\Scripts\Activate.ps1`; Windows CMD: `.venv\Scripts\activate.bat`; macOS/Linux: `source .venv/bin/activate`.

```sh
python -m pip install -r requirements.txt
```

Copie `.env.example` para `.env`. Configure `MYSQL_HOST` e `MYSQL_PORT` conforme seu servidor MySQL (em instalações locais, normalmente `127.0.0.1:3306`). Preencha também `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` e `SECRET_KEY`. O arquivo é lido automaticamente. `MYSQL_ROOT_PASSWORD` só é usado no Docker. `COOKIE_SECURE=0` permite a demonstração local por HTTP.

No Windows, você também pode abrir `Iniciar-MySQL-Local.bat` com o MySQL instalado e em execução. Se a conexão atual falhar, o iniciador pede os dados da conexão que funciona no MySQL Workbench. Ele salva a configuração no `.env` e abre o navegador quando a base estiver pronta. Se a base ainda estiver vazia, siga a preparação abaixo. A senha digitada é a senha do MySQL. O cadastro de cozinheiro e a senha de administrador do site são separados.

Para só testar a configuração local, rode `python -m scripts.iniciar_mysql_local --verificar`. O iniciador para o MySQL local prioriza o `.env` da pasta. Ao rodar o Flask diretamente pelo VS Code, reinicie o servidor após corrigir o arquivo e confira se a configuração do VS Code define valores diferentes.

Para uma **base nova e vazia**, com um usuário autorizado a criar as tabelas:

```sh
python -m scripts.preparar_banco
python -m scripts.criar_admin
python -m flask --app app:create_app run --port 5055
```

Abra **http://127.0.0.1:5055**. A rota `/api/health` consulta o MySQL e retorna 503 se o banco estiver desligado, o acesso for recusado ou a tabela inicial não existir. O preparador recusa uma base que já contém tabelas. Se a base já foi preparada, não repita a preparação.

Se usar o MySQL Workbench, pode executar manualmente `database/01_modelo_fisico.sql`, `database/20_triggers.sql` e `database/02_insercoes_basicas.sql`, nessa ordem. **O script físico original apaga e recria as tabelas de `sabor_clic`; use apenas em uma base descartável ou nova.** O preparador Python evita essa exclusão acidental.

## Roteiro de demonstração

1. Cadastre um cliente e entre na conta.
2. Cadastre um cozinheiro pela área correspondente. Ele fica pendente.
3. Entre como administrador, aprove o cozinheiro e anote a senha provisória apresentada uma única vez. Entregue-a pessoalmente ao cozinheiro.
4. Entre como cozinheiro e troque a senha provisória.
5. Como cliente, adicione pratos ao carrinho e finalize o pedido.
6. Como cozinheiro, informe os minutos e avance: Recebido → Em Preparo → Pronto → Entregue.
7. Acompanhe a atualização automática na tela do cliente. Reiniciar o Flask não apaga o pedido.
8. No administrador, cadastre/edite/inative um prato e altere seus dados pessoais.

O preço, a identidade do cliente e o total usados para gravar o pedido vêm do servidor. Pratos referenciados em pedidos ou fichas técnicas não podem ser excluídos: use **Inativar** para retirá-los do cardápio preservando o histórico.

## Estoque, locações e relatórios

A ficha técnica relaciona cada prato aos ingredientes e quantidades consumidas. Ao iniciar o preparo, a trigger baixa o estoque uma única vez por pedido. Se faltar algum ingrediente, toda a operação é desfeita e a cozinha recebe um aviso.

O catálogo possui interface; a manutenção de **ingredientes, fichas técnicas e locações é feita por SQL** nesta versão, pois o frontend original não contém essas telas. Ao cadastrar novos pratos, cadastre também sua ficha técnica no banco para que a baixa de seus ingredientes seja calculada. Não confunda cadastro de prato com cadastro da receita.

Execute `database/11_queries_relatorios.sql` no Workbench para consultar vendas por prato, estoque mínimo, pedidos/itens, ocupação das bancadas e totais. As triggers de locação impedem períodos sobrepostos; horários consecutivos são aceitos e locações canceladas não bloqueiam horários.

## Organização MVC

- `models/banco.py`: conexão e transações MySQL; commit ou rollback e fechamento da conexão.
- `models/loja.py`: operações de persistência e regras dos pedidos.
- `controllers/api.py`: rotas, validação, sessões e autorização por perfil.
- `views/respostas.py`: mensagens Flash do Flask convertidas em JSON, consumidas na própria resposta.
- `templates/` e `static/`: apresentação original e comunicação assíncrona.
- `models/memoria.py`: legado da Parte 1 preservado; não é utilizado pela aplicação integrada.
- `database/`: os quatro entregáveis SQL.
- `docs/VALIDACAO.md`: resultados executados, correções e limites da validação.

## Segurança implementada

Senhas em hash scrypt do Werkzeug; sessões assinadas com validade de 8 horas; cookie HttpOnly/SameSite=Lax; verificação do perfil e da conta ativa em cada operação protegida; troca obrigatória da senha provisória; bloqueio de origens externas nas operações de escrita; limites e tipos dos campos; consultas SQL parametrizadas; propriedade dos pedidos do cliente; respostas sem hashes de senha; conteúdo da interface inserido como texto; rollback de transações inválidas.

`SECRET_KEY` deve ser fixa e privada para manter sessões entre reinícios. Em HTTPS, use `COOKIE_SECURE=1`. O servidor incluído serve à demonstração local. Publicação aberta exige servidor de produção, HTTPS, backups e proteção contra tentativas repetidas de login. Não foram realizados teste de carga ou auditoria externa de segurança.

## Repetir os testes

Instale as ferramentas de desenvolvimento:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest tests/test_api.py tests/test_regressoes.py -q
node --test tests/test_models.cjs
```

Os testes acima não precisam de MySQL. Para a validação real, crie uma base **separada e descartável** chamada `sabor_clic_test`; dê ao usuário de teste permissão para criar/apagar tabelas e triggers nela. Configure a conexão e `MYSQL_DATABASE=sabor_clic_test`, `SABOR_TESTES=1` no ambiente. O sufixo `_test` e a autorização explícita são obrigatórios. **Essa base é recriada a cada teste. Nunca aponte os testes para dados que deseja conservar.**

macOS/Linux:

```sh
export MYSQL_DATABASE=sabor_clic_test
export SABOR_TESTES=1
python -m pytest tests/test_mysql.py -q
python -m playwright install chromium
python -m pytest tests/test_browser.py -q
```

PowerShell: use `$env:MYSQL_DATABASE = "sabor_clic_test"` e `$env:SABOR_TESTES = "1"` antes dos mesmos comandos Python. Também é possível usar Chrome já instalado, definindo `CHROME_EXECUTABLE` com o caminho do executável. As capturas do teste de navegador ficam em `docs/evidencias/` durante a execução.

Os SQL de relatórios podem ser executados separadamente. Os resultados executados estão em `docs/VALIDACAO.md`.
