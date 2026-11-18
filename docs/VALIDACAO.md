# Validação da Parte 2

Validação realizada em 18/11/2026 com MySQL 8.4.13, Flask e Chrome.

- **55 testes Python aprovados**, cobrindo cadastro, login, sessão, permissões por perfil, pedidos, cardápio, relatórios e integridade do banco.
- **4 testes JavaScript aprovados**, cobrindo as classes, o carrinho, a serialização e o fluxo de status.
- O fluxo no navegador incluiu cadastro do cliente, aprovação do cozinheiro, troca de senha, pedido, preparo e entrega.
- Foram verificados estoque insuficiente, disputa de estoque entre pedidos, bloqueio de alteração após a baixa e conflito de horários de locação.
- O iniciador foi executado em uma pasta limpa. Ele preparou o banco e criou o acesso administrativo sem configuração manual.
- O fluxo dos três perfis também foi concluído nessa instalação, usando o acesso gerado pelo iniciador. Após parar e abrir novamente, a conta do cliente e o pedido entregue continuaram salvos.
- A configuração para MySQL instalado no computador foi testada com conexão inválida, correção das credenciais e leitura do arquivo `.env`.

Os testes de execução foram feitos no macOS. Os arquivos de abertura do Windows usam os mesmos programas em Python, mas ainda precisam de execução em um computador Windows.

A manutenção de ingredientes, fichas técnicas e locações é feita por SQL. O sistema foi preparado para demonstração local.
