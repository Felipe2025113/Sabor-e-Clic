# Sabor & Clic — Parte 1

Projeto integrador com frontend em HTML, CSS e JavaScript e um backend inicial em Python/Flask.

## Executar localmente

É necessário Python 3.9 ou superior. Na pasta do projeto:

```bash
python -m venv .venv
```

Ative o ambiente no Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Ou no Linux/macOS:

```bash
source .venv/bin/activate
```

Instale a dependência e inicie o servidor:

```bash
python -m pip install -r requirements.txt
python app.py
```

- Site existente: http://127.0.0.1:5000/
- Demonstração da integração com Flask: http://127.0.0.1:5000/demo-api
- Verificação do servidor: http://127.0.0.1:5000/api/health

Abra as páginas pelo servidor, pois a navegação usa caminhos a partir da raiz do site.

## Backend inicial

A organização segue uma separação simples de responsabilidades:

- `app.py`: configura o Flask e serve as páginas existentes.
- `models/memoria.py`: dados simulados, cálculo do pedido e regras básicas.
- `controllers/api.py`: recebe requisições e define os endpoints.
- `views/respostas.py`: padroniza a apresentação das respostas JSON.
- `templates/demo_api.html` e `static/js/demo_api.js`: demonstração de GET e POST com Fetch.

| Método | Rota | Função |
| --- | --- | --- |
| GET | `/api/health` | Verificar o serviço |
| GET | `/api/pratos` | Listar os três pratos de exemplo |
| GET | `/api/pedidos` | Listar pedidos em memória |
| GET | `/api/pedidos/<id>` | Consultar um pedido |
| POST | `/api/pedidos` | Criar pedido |
| PATCH | `/api/pedidos/<id>/status` | Avançar o status |

POST e PATCH recebem `Content-Type: application/json`.

Exemplo do corpo de `POST /api/pedidos`:

```json
{
  "cliente": "Cliente Teste",
  "endereco": "Rua de teste, 10",
  "itens": [{"prato_id": 1, "quantidade": 2}]
}
```

O servidor consulta o preço do prato e calcula o total; valores de preço enviados pelo cliente não são usados. A resposta de criação tem código HTTP 201 e formato `{"sucesso": true, "dados": {...}}`. Erros de validação retornam 400 e `{"sucesso": false, "erro": "mensagem"}`. Pedidos inexistentes retornam 404.

Exemplo de `PATCH /api/pedidos/1/status`:

```json
{"status": "Em Preparo", "tempoEstimado": 20}
```

O fluxo é `Pedido recebido` → `Em Preparo` → `Pronto para Entrega` → `Entregue`. O início do preparo exige tempo inteiro positivo em minutos. Para os dois últimos estados, basta enviar `status`.

## Limitações previstas nesta etapa

Este é um protótipo acadêmico para demonstração local com dados fictícios.

- Os pedidos da API ficam em memória e são apagados ao reiniciar o servidor.
- As telas originais de cliente, administrador e cozinheiro continuam usando `localStorage`/`sessionStorage`. Seus dados não são sincronizados com a API; a integração inicial está em `/demo-api`.
- Ainda não há login real, autorização por perfil, banco relacional, agendamentos, estoque ou CRUD de pratos na API.
- A memória não é adequada para múltiplos processos e acessos concorrentes de produção.
- A integração completa das telas e a persistência ficam para a continuação do projeto.

## Verificação

```bash
python -m unittest discover -s tests -v
```

Os testes cobrem criação e consulta, preço calculado pelo servidor, entradas inválidas, transições de status, reinicialização da memória e acesso às páginas existentes.

Referência: [documentação oficial do Flask](https://flask.palletsprojects.com/en/stable/quickstart/).
