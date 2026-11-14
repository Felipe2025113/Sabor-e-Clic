# Validação da Parte 2

A base deste trabalho foi o commit `041c91c` do repositório, baixado do GitHub em 14/11/2026. Foram comparados os seis arquivos HTML, o CSS e a imagem com essa versão. Os oito arquivos são idênticos.

| Verificação | Na versão anterior do GitHub | Com a integração |
|---|---|---|
| Telas de cadastro | Flask retornava 404 | Flask entrega as duas telas |
| Login e sessão | Rotas do JavaScript retornavam 404 | Login e sessão passam pelo MySQL e pelas permissões de cada perfil |
| Cardápio | Estrutura JSON incompatível com o JavaScript | A API entrega a lista esperada pela interface |
| Avanço do pedido | O método PUT retornava 405 | O cozinheiro prepara e entrega o pedido pelo mesmo fluxo da tela |
| Instalação | Backend em memória, pasta do banco vazia | O iniciador prepara o esquema, os dados básicos e as nove triggers |
| Banco indisponível | Na integração enviada anteriormente, a checagem retornava 200 sem MySQL | A checagem consulta a tabela de usuários e retorna 503 durante a falha |

Os testes executados incluíram **54 testes Python** com Flask, MySQL 8.4.13 e fluxo real no Chrome, além de **4 testes JavaScript**. Os testes verificaram cadastros, sessões, permissões, cardápio, transições do pedido, persistência, relatórios, estoque insuficiente e conflito de horários de locação.

O iniciador foi executado no macOS a partir de uma cópia nova e com Docker. Os arquivos de dados e a senha de administrador da instalação são gerados ao iniciar. O arquivo `Iniciar.bat` chama o mesmo iniciador em Python. A execução pelo arquivo do Windows não foi testada em um computador Windows.

As locações, os ingredientes e as fichas técnicas são administrados por SQL nesta versão. Os relatórios estão em `database/11_queries_relatorios.sql`. O projeto foi validado para demonstração local.
