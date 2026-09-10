function adicionarAoCarrinho(idPrato) {
  const pratoEncontrado = pratosDisponiveis.find(prato => prato.id === idPrato)
  if (pratoEncontrado === undefined) return
  const itemNoCarrinho = carrinho.find(item => item.id === idPrato)

  if (itemNoCarrinho !== undefined) {
    itemNoCarrinho.quantidade += 1
  } else {
    carrinho.push({
      id: pratoEncontrado.id,
      nome: pratoEncontrado.nome,
      preco: pratoEncontrado.preco,
      quantidade: 1
    })
  }

  renderizarCarrinho()
}




function removerDoCarrinho(idPrato) {
  const itemNoCarrinho = carrinho.find(item => item.id === idPrato)
  if (itemNoCarrinho) {
    if (itemNoCarrinho.quantidade > 1) {
      itemNoCarrinho.quantidade -= 1
    } else {
      carrinho = carrinho.filter(item => item.id !== idPrato)
    }
  }
  renderizarCarrinho()
}



function gerarNovoIdPedido() {
  if (pedidos.length === 0) return 1
  const idsExistentes = pedidos.map(pedido => pedido.id)
  return Math.max(...idsExistentes) + 1
}





function validarFormulario(event) {
  event.preventDefault()
  if (carrinho.length === 0) {
    alert("Adicione pelo menos um item ao carrinho!")
    return
  }

  const campos = {
    nome: document.getElementById("nome").value.trim(),
    email: document.getElementById("email").value.trim(),
    endereco: document.getElementById("endereco").value.trim()
  }

  let formularioValido = true

  const gerenciarErro = (idErro, mostrar) => {
    document.getElementById(idErro).style.display = mostrar ? "inline" : "none"
    if (mostrar) formularioValido = false
  }

  const nomeInvalido = campos.nome === "" || campos.nome.length < 3
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  const emailInvalido = campos.email === "" || !emailRegex.test(campos.email)
  const enderecoInvalido = campos.endereco === "" || campos.endereco.length < 3
  gerenciarErro("erro-nome", nomeInvalido)
  gerenciarErro("erro-email", emailInvalido)
  gerenciarErro("erro-endereco", enderecoInvalido)

  if (!formularioValido) return

  const novoPedido = {
    id: gerarNovoIdPedido(),
    cliente: campos.nome,
    endereco: campos.endereco,
    itens: [...carrinho],
    status: "Pedido recebido",
    tempoEstimado: null
  }

  pedidos.push(novoPedido)
  salvarPedidos()

  const meusIds = JSON.parse(sessionStorage.getItem("meusPedidosIds") || "[]")
  meusIds.push(novoPedido.id)
  sessionStorage.setItem("meusPedidosIds", JSON.stringify(meusIds))

  carrinho = []
  renderizarCarrinho()
  renderizarMeusPedidos()
  alert("Pedido realizado com sucesso!")
}


function renderizarMeusPedidos() {
  const colunas = {
    "Pedido recebido": document.getElementById("kds-col-aguardando"),
    "Em Preparo": document.getElementById("kds-col-preparo"),
    "Pronto para Entrega": document.getElementById("kds-col-pronto"),
    "Entregue": document.getElementById("kds-col-entregue")
  }

  const contadores = {
    "Pedido recebido": document.getElementById("kds-count-aguardando"),
    "Em Preparo": document.getElementById("kds-count-preparo"),
    "Pronto para Entrega": document.getElementById("kds-count-pronto"),
    "Entregue": document.getElementById("kds-count-entregue")
  }

  const vazio = document.getElementById("meus-pedidos-vazio")
  const meusIds = JSON.parse(sessionStorage.getItem("meusPedidosIds") || "[]")

  pedidos = carregarPedidos()
  const meusPedidos = pedidos.filter(pedido => meusIds.includes(pedido.id))

  Object.values(colunas).forEach(coluna => coluna.innerHTML = "")

  vazio.hidden = meusPedidos.length !== 0

  const totais = { "Pedido recebido": 0, "Em Preparo": 0, "Pronto para Entrega": 0, "Entregue": 0 }

  meusPedidos.forEach(pedido => {
    const coluna = colunas[pedido.status] || colunas["Pedido recebido"]
    totais[pedido.status] = (totais[pedido.status] || 0) + 1

    const divPedido = document.createElement("div")
    divPedido.className = `kds-cartao ${classeStatus(pedido.status)}`

    let listaItens = ""
    for (const item of pedido.itens) {
      listaItens += `<li>${item.quantidade}x ${item.nome}</li>`
    }

    const tempo = pedido.tempoEstimado
      ? `<span class="pedido-tempo">Tempo estimado: <strong>${pedido.tempoEstimado} min</strong></span>`
      : ""

    divPedido.innerHTML = `
      <div class="linha-pedido-topo">
        <span class="pedido-numero">Pedido #${pedido.id}</span>
      </div>
      <ul class="pedido-itens-lista">${listaItens}</ul>
      ${tempo}
    `

    coluna.appendChild(divPedido)
  })

  Object.keys(contadores).forEach(status => {
    contadores[status].textContent = totais[status]
  })
}

window.onload = function () {
  renderizarCardapio()
  renderizarCarrinho()
  renderizarMeusPedidos()

  const formPedido = document.getElementById("form-pedido")
  formPedido.onsubmit = validarFormulario

  setInterval(renderizarMeusPedidos, 5000)
}
