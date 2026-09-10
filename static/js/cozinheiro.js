function criarLinhaPedido(pedido) {
  const divPedido = document.createElement("div")
  divPedido.className = `linha-pedido-cozinha ${classeStatus(pedido.status)}`

  let listaItens = ""
  for (const item of pedido.itens) {
    listaItens += `<li>${item.quantidade}x ${item.nome}</li>`
  }

  let botoes = ""
  if (pedido.status === "Pedido recebido") {
    botoes = `<button class="btn-avancar-status" onclick="iniciarPreparo(${pedido.id})">Iniciar Preparo</button>`
  } else if (pedido.status === "Em Preparo") {
    botoes = `<button class="btn-avancar-status" onclick="marcarPronto(${pedido.id})">Marcar como Pronto</button>`
  } else if (pedido.status === "Pronto para Entrega") {
    botoes = `<button class="btn-avancar-status" onclick="marcarEntregue(${pedido.id})">Marcar como Entregue</button>`
  }


  const tempo = pedido.tempoEstimado ? ` · tempo estimado: ${pedido.tempoEstimado} min` : ""



  divPedido.innerHTML = `
    <div class="info-pedido-cozinha">
      <div class="linha-pedido-topo">
        <span class="pedido-numero">Pedido #${pedido.id} - ${pedido.cliente}</span>
        <span class="status-badge ${classeStatus(pedido.status)}">${pedido.status}</span>
      </div>
      <ul class="pedido-itens-lista">${listaItens}</ul>
      <span class="pedido-tempo">Endereço: ${pedido.endereco}${tempo}</span>
    </div>
    <div class="acoes-pedido-cozinha">${botoes}</div>
  `

  return divPedido
}




function renderizarFila() {
  pedidos = carregarPedidos()

  const containerFila = document.getElementById("fila-pedidos")
  containerFila.innerHTML = ""

  const pedidosPendentes = pedidos.filter(
    pedido => pedido.status !== "Pronto para Entrega" && pedido.status !== "Entregue"
  )

  if (pedidosPendentes.length === 0) {
    containerFila.innerHTML = "<p class='fila-vazia'>Nenhum pedido na fila.</p>"
    return
  }

  pedidosPendentes.forEach(pedido => containerFila.appendChild(criarLinhaPedido(pedido)))
}





function renderizarProntos() {
  pedidos = carregarPedidos()

  const containerProntos = document.getElementById("fila-prontos")
  containerProntos.innerHTML = ""

  const pedidosProntos = pedidos.filter(pedido => pedido.status === "Pronto para Entrega")

  if (pedidosProntos.length === 0) {
    containerProntos.innerHTML = "<p class='fila-vazia'>Nenhum pedido pronto no momento.</p>"
    return
  }

  pedidosProntos.forEach(pedido => containerProntos.appendChild(criarLinhaPedido(pedido)))
}





function iniciarPreparo(idPedido) {
  const pedido = pedidos.find(p => p.id === idPedido)
  if (pedido == undefined) return

  const tempo = prompt("Tempo estimado de preparo (em minutos):")
  if (tempo === null || tempo === "") return

  pedido.status = "Em Preparo"
  pedido.tempoEstimado = parseInt(tempo)

  salvarPedidos()
  renderizarFila()
  renderizarProntos()
}




function marcarPronto(idPedido) {
  const pedido = pedidos.find(p => p.id === idPedido)
  if (pedido == undefined) return

  pedido.status = "Pronto para Entrega"
  salvarPedidos()
  renderizarFila()
  renderizarProntos()
}




function marcarEntregue(idPedido) {
  const pedido = pedidos.find(p => p.id === idPedido)
  if (pedido == undefined) return

  pedido.status = "Entregue"
  salvarPedidos()
  renderizarProntos()
}



window.onload = function () {
  verificarAcesso("COZINHEIRO")
  renderizarFila()
  renderizarProntos()
  setInterval(function () {
    renderizarFila()
    renderizarProntos()
  }, 5000)
}
