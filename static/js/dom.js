function renderizarCardapio() {
  const conteinerCardapio = document.getElementById("lista-pratos")
  conteinerCardapio.innerHTML = ""

  pratosDisponiveis.forEach((prato) => {
    const { id, nome, descricao, preco } = prato

    const divPrato = document.createElement("div")
    divPrato.className = "item-cardapio"
    divPrato.innerHTML = `
      <div>
        <h3>${nome}</h3>
        <p>${descricao}</p>
        <p><strong>R$ ${preco.toFixed(2)}</strong></p>
      </div>
      <div class="acoes-item">
        <button class="btn-avancar-status" onclick="adicionarAoCarrinho(${id})">Adicionar ao Carrinho</button>
      </div>
    `

    conteinerCardapio.appendChild(divPrato)
  })
}

function renderizarCarrinho() {
  const conteinerCarrinho = document.getElementById("itens-carrinho")
  const Total = document.getElementById("valor-total")

  if (carrinho.length === 0) {
    conteinerCarrinho.innerHTML = "<p class='fila-vazia'>Seu carrinho está vazio.</p>"
    Total.innerText = "0.00"
    return
  }

  conteinerCarrinho.innerHTML = ""

  for (const item of carrinho) {
    const subtotal = item.preco * item.quantidade

    const divItem = document.createElement("div")
    divItem.className = "item-carrinho"
    divItem.innerHTML = `
      <p><strong>${item.nome}</strong></p>
      <p>Qtd: ${item.quantidade} x R$ ${item.preco.toFixed(2)} = Subtotal: R$ ${subtotal.toFixed(2)}</p>
      <button class="btn-avancar-status" onclick="removerDoCarrinho(${item.id})">Remover 1 unidade</button>
    `

    conteinerCarrinho.appendChild(divItem)
  }

  const total = calcularTotalCarrinho()
  Total.innerText = total.toFixed(2)
}

function calcularTotalCarrinho() {
  let total = 0
  for (const i in carrinho) {
    total += carrinho[i].preco * carrinho[i].quantidade
  }
  return total
}
