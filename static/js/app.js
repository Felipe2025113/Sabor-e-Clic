function adicionarAoCarrinho(idPrato) {
  let pratoEncontrado = null
  for (let prato of pratosDisponiveis) {
    if (prato.id === idPrato) {
      pratoEncontrado = prato
      break
    }
  }

  if (pratoEncontrado === null) return

    let itemNoCarrinho = null
    for (let item of carrinho) {
        if (item.id === idPrato) {
        itemNoCarrinho = item
        break
    }
  }

  if (itemNoCarrinho !== null) {
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

  if (formularioValido) {
    const novoPedido = {
      id: pedidos.length + 1,
      nome_cliente: campos.nome,
      endereco: campos.endereco,
      itens: [...carrinho],
      status: "Aguardando"
    }
    pedidos.push(novoPedido)
    alert("Pedido realizado com sucesso!")
  }
}


window.onload = function () {
  renderizarCardapio()
  renderizarCarrinho()

  const formPedido = document.getElementById("form-pedido")
  formPedido.onsubmit = validarFormulario
}
