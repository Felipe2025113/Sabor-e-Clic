# Sabor & Clic

Projeto Integrador — Parte 2 · IFSP

Sistema de pedidos para uma dark kitchen, com cadastro de clientes e cozinheiros, gerenciamento do cardápio, acompanhamento do preparo e controle de acesso por perfil. Desenvolvido em HTML, CSS, JavaScript, Flask e MySQL.

## Como testar

O caminho mais simples usa **Python 3.10 ou superior** e **Docker Desktop**. O iniciador prepara o banco, carrega os dados e abre o site.

1. [Baixe a entrega em ZIP](https://github.com/Felipe2025113/Sabor-e-Clic/releases/latest/download/Sabor-e-Clic-Parte-2.zip) e extraia a pasta.
2. Abra o Docker Desktop e aguarde a inicialização.
3. No Windows, dê dois cliques em **Iniciar.bat**. No macOS, abra **Iniciar.command**. No Linux, execute `python3 -m scripts.iniciar` dentro da pasta.
4. Aguarde o navegador abrir. A primeira execução precisa de internet para baixar as dependências.

O terminal mostra o endereço do site e a senha inicial de **admin@saborclic.local**. Para acessar o painel administrativo, entre pela **Área do Cliente** com essas credenciais.

Os cadastros e pedidos são mantidos entre as execuções. Para parar, execute `python -m scripts.iniciar --parar` na mesma pasta. No macOS/Linux, use `python3`.

## Roteiro de teste

Para usar os perfis ao mesmo tempo, abra navegadores diferentes ou perfis separados do navegador. Você também pode sair de uma conta e entrar em outra.

| Perfil | O que testar |
|---|---|
| Cliente | Cadastre uma conta, entre, adicione pratos ao carrinho e confirme o pedido. |
| Administrador | Use o acesso mostrado no terminal. Cadastre ou edite um prato e aprove o cadastro de um cozinheiro. |
| Cozinheiro | Solicite o cadastro pela Área do Cozinheiro. Após a aprovação, use a senha provisória apresentada ao administrador e troque-a no primeiro acesso. |

Na cozinha, informe o tempo de preparo e avance o pedido por **Recebido → Em Preparo → Pronto → Entregue**. A tela do cliente acompanha essas mudanças automaticamente.

## MySQL instalado no computador

Para executar pelo Python ou pelo VS Code com um MySQL próprio, consulte as [instruções de configuração](docs/EXECUCAO.md#alternativa-python-e-mysql-instalados). No Windows, o arquivo **Iniciar-MySQL-Local.bat** testa essa conexão e pede as credenciais do MySQL quando necessário.

## Banco de dados e testes

Os quatro scripts SQL ficam em `database/`. Eles contêm o modelo físico, os dados iniciais, os relatórios e as triggers de estoque, total do pedido e conflito de locações.

A manutenção de ingredientes, fichas técnicas e locações é feita por SQL. Novos pratos precisam da ficha técnica para descontar seus ingredientes do estoque.

Os testes automatizados estão em `tests/`. As [instruções de execução](docs/EXECUCAO.md#repetir-os-testes) e os [resultados da validação](docs/VALIDACAO.md) estão na pasta `docs/`.
