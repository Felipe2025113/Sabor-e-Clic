window.onload = function () {
  verificarAcesso("ADM")
  renderizarCatalogoAdm()
}

let idEmEdicao = null

function gerarNovoId() {
  if (pratosDisponiveis.length === 0) return 1
  const idsExistentes = pratosDisponiveis.map(prato => prato.id)
  return Math.max(...idsExistentes) + 1
}



function cadastrarPrato(nome, descricao, preco, categoria) {
  if (nome.trim() === "" || preco === "") {
    alert("Preencha o nome e preço do prato")
    return
  }

  const novoPrato = {
    id: gerarNovoId(),
    nome: nome,
    descricao: descricao,
    preco: parseFloat(preco),
    categoria: categoria
  }

  pratosDisponiveis.push(novoPrato)
  salvarPratos()
  renderizarCatalogoAdm()
  alert("Prato cadastrado com sucesso!")
}






function editarPrato(idPrato, novosDados) {
  const prato = pratosDisponiveis.find(p => p.id === idPrato)

  if (prato == undefined) {
    alert("Prato não encontrado")
    return
  }

  if (novosDados.nome !== undefined) prato.nome = novosDados.nome
  if (novosDados.descricao !== undefined) prato.descricao = novosDados.descricao
  if (novosDados.preco !== undefined) prato.preco = parseFloat(novosDados.preco)
  if (novosDados.categoria !== undefined) prato.categoria = novosDados.categoria

  salvarPratos()
  renderizarCatalogoAdm()
  alert("Prato atualizado com sucesso")
}





function removerPratoDoCatalogo(idPrato) {
  const index = pratosDisponiveis.findIndex(p => p.id === idPrato)
  if (index !== -1) {
    pratosDisponiveis.splice(index, 1)
    salvarPratos()
    renderizarCatalogoAdm()
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
    alert("Nenhum prato selecionado para edição")
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







function renderizarCatalogoAdm() {
  const container = document.getElementById("lista-pratos-adm")
  container.innerHTML = ""

  pratosDisponiveis.forEach(prato => {
    const divPrato = document.createElement("div")
    divPrato.className = "item-cardapio"
    divPrato.innerHTML = `
      <div>
        <h3>${prato.nome}</h3>
        <p>${prato.descricao}</p>
        <p><strong>R$ ${prato.preco.toFixed(2)}</strong> · ${prato.categoria}</p>
      </div>
      <div class="acoes-item">
        <button class="btn-avancar-status" onclick="abrirEdicao(${prato.id})">Editar</button>
        <button class="btn-avancar-status" onclick="removerPratoDoCatalogo(${prato.id})">Remover</button>
      </div>
    `
    container.appendChild(divPrato)
  })
}
