const CHAVE_PRATOS = "saborclic_pratos"
const CHAVE_PEDIDOS = "saborclic_pedidos"
const pratosSeed = [
  {
    id: 1,
    nome: "Marmita Gourmet - Strogonoff de Filé",
    descricao: "Acompanha arroz branco e batata palha artesanal.",
    preco: 32.90,
    categoria: "Almoço"
  },
  {
    id: 2,
    nome: "Feijoada Completa Individual",
    descricao: "Acompanha couve refogada, farofa e laranja.",
    preco: 38.50,
    categoria: "Almoço"
  },
  {
    id: 3,
    nome: "Suco Natural de Laranja (500ml)",
    descricao: "Suco 100% natural, sem adição de açúcar.",
    preco: 9.00,
    categoria: "Bebidas"
  }
]



function carregarPratos() {
  const salvo = localStorage.getItem(CHAVE_PRATOS)
  return salvo ? JSON.parse(salvo) : pratosSeed
}

function carregarPedidos() {
  const salvo = localStorage.getItem(CHAVE_PEDIDOS)
  return salvo ? JSON.parse(salvo) : []
}




function salvarPratos() {
  localStorage.setItem(CHAVE_PRATOS, JSON.stringify(pratosDisponiveis))
}

function salvarPedidos() {
  localStorage.setItem(CHAVE_PEDIDOS, JSON.stringify(pedidos))
}




function classeStatus(status) {
  const mapa = {
    "Pedido recebido": "aguardando",
    "Em Preparo": "preparo",
    "Pronto para Entrega": "pronto",
    "Entregue": "entregue"
  }
  return mapa[status] || "aguardando"
}

let pratosDisponiveis = carregarPratos()
let carrinho = []
let pedidos = carregarPedidos()
