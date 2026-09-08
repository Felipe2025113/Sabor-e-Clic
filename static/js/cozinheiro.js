function renderizarFila() {
  const containerFila = document.getElementById("fila-pedidos")
  containerFila.innerHTML = ""

  const pedidosPendentes = pedidos.filter(pedido => pedido.status !== "Pronto para Entrega")

  if (pedidosPendentes.length === 0) {
    containerFila.innerHTML = "<p>Nenhum pedido na fila.</p>"
    return
  }

  pedidosPendentes.forEach(pedido => {
    const divPedido = document.createElement("div")

    let listaItens = ""
    for (const item of pedido.itens) {
      listaItens += `<li>${item.quantidade}x ${item.nome}</li>`
    }

    divPedido.innerHTML = `
      <h3>Pedido #${pedido.id} - ${pedido.cliente}</h3>
      <ul>${listaItens}</ul>
      <p>Status: <strong>${pedido.status}</strong></p>
      <button onclick="iniciarPreparo(${pedido.id})">
      <button onclick="marcarPronto(${pedido.id})">Marcar como Pronto</button>
      <hr>
    `

    containerFila.appendChild(divPedido)
  })
}

function iniciarPreparo(idPedido) {
  const pedido = pedidos.find(p => p.id === idPedido)
  if (pedido == undefined) return

  const tempo = prompt("Tempo estimado de preparo (em minutos):")
  if (tempo === null || tempo === "") return

  pedido.status = "Em Preparo"
  pedido.tempoEstimado = parseInt(tempo)

  renderizarFila()
}

function marcarPronto(idPedido) {
  const pedido = pedidos.find(p => p.id === idPedido)
  if (pedido == undefined) return

  pedido.status = "Pronto para Entrega"
  renderizarFila()
}

window.onload = function () {
  verificarAcesso("COZINHEIRO")
  renderizarFila()
}
