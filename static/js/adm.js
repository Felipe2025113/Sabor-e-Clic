window.onload = function () {
  verificarAcesso("ADM")
  renderizarCardapio()
}

let idEmEdicao = null

function gerarNovoId() {
  if (pratosDisponiveis.length === 0) return 1
  const idsExistentes = pratosDisponiveis.map(prato => prato.id)
  return Math.max(...idsExistentes) + 1
}

function cadastrarPrato(nome, descricao, preco, categoria){
    const novoPrato = {
        id: gerarNovoId(),
        nome: nome,
        descricao: descricao,
        preco: parseFloat(preco),
        categoria: categoria
    }
    pratosDisponiveis.push(novoPrato)
    renderizarCardapio()
    alert("Prato cadastrado com sucesso!")
}

function editarPrato(idPrato, novosDados) {
  const prato = pratosDisponiveis.find(p => p.id === idPrato)

  if (prato == undefined) {
    alert("Prato não encontrado!")
    return
  }

  if (novosDados.nome !== undefined) prato.nome = novosDados.nome
  if (novosDados.descricao !== undefined) prato.descricao = novosDados.descricao
  if (novosDados.preco !== undefined) prato.preco = parseFloat(novosDados.preco)
  if (novosDados.categoria !== undefined) prato.categoria = novosDados.categoria

  renderizarCardapio()
  alert("Prato atualizado com sucesso!")
}

function removerPratoDoCatalogo(idPrato) {
  const index = pratosDisponiveis.findIndex(p => p.id === idPrato)
  if (index !== -1) {
    pratosDisponiveis.splice(index, 1)
    renderizarCardapio()
    alert("Prato removido do catálogo!")
  }
}

function abrirEdicao(idPrato) {
  const prato = pratosDisponiveis.find(p => p.id === idPrato)
  if (prato == undefined) return

  idEmEdicao = idPrato

  document.getElementById("edit-nome").value = prato.nome
  document.getElementById("edit-descricao").value = prato.descricao
  document.getElementById("edit-preco").value = prato.preco
  document.getElementById("edit-categoria").value = prato.categoria
}

function salvarEdicao() {
  if (idEmEdicao == null) {
    alert("Nenhum prato selecionado para edição!")
    return
  }

  editarPrato(idEmEdicao, {
    nome: document.getElementById("edit-nome").value,
    descricao: document.getElementById("edit-descricao").value,
    preco: document.getElementById("edit-preco").value,
    categoria: document.getElementById("edit-categoria").value
  })

  idEmEdicao = null
}