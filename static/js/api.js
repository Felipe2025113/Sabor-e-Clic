async function requisicao(caminho, { metodo = "GET", corpo = null } = {}){
    const opcoes = {
        method: metodo,
        headers: {}
    }
    if (corpo !== null){
        opcoes.headers["Content-Type"] = "application/json"
        opcoes.body = JSON.stringify(corpo)
    }

    let resposta
    try{
        resposta = await fetch(caminho, opcoes)
    } catch (erroRede){
        throw new Error("Não foi possível conectar ao servidor")
    }

    const dados = await resposta.json().catch(() => null)
    if (!resposta.ok){
        const erro = new Error(dados?.erro || dados?.mensagem || "Ocorreu um erro na requisição")
        erro.status = resposta.status
        throw erro
    }

    return dados
}

async function apiLogin(credenciais){
    const dados = await requisicao("/api/login", {
        metodo: "POST",
        corpo: credenciais
    })
    return Usuario.deJSON(dados)
}

async function apiLogout(){
    return await requisicao("/api/logout", {
        metodo: "POST"
    })
}

async function apiUsuarioAtual(){
    const dados = await requisicao("/api/me")
    return Usuario.deJSON(dados)
}

async function apiCadastrarCliente(cadastro){
    return await requisicao("/api/clientes", {
        metodo: "POST",
        corpo: cadastro
    })
}

async function apiCadastrarCozinheiro(cadastro){
    return await requisicao("/api/cozinheiros", {
        metodo: "POST",
        corpo: cadastro
    })
}

async function apiAlterarSenha(alteracao){
    return await requisicao("/api/senha", {
        metodo: "PUT",
        corpo: alteracao
    })
}

async function apiBuscarPratos(){
    const dados = await requisicao("/api/pratos")
    return dados.map(item => Prato.deJSON(item))
}

async function apiCriarPrato(prato){
    const dados = await requisicao("/api/pratos", {
        metodo: "POST",
        corpo: prato
    })
    return Prato.deJSON(dados)
}

async function apiAtualizarPrato(id, prato){
    const dados = await requisicao(`/api/pratos/${id}`, {
        metodo: "PUT",
        corpo: prato
    })
    return Prato.deJSON(dados)
}

async function apiRemoverPrato(id){
    return await requisicao(`/api/pratos/${id}`, {
        metodo: "DELETE"
    })
}

async function apiCriarPedido(pedido){
    const dados = await requisicao("/api/pedidos", {
        metodo: "POST",
        corpo: {
            endereco: pedido.endereco,
            itens: pedido.itens.map(item => ({ id: item.id, quantidade: item.quantidade }))
        }
    })
    return Pedido.deJSON(dados)
}

async function apiBuscarPedidos(){
    const dados = await requisicao("/api/pedidos")
    return dados.map(item => Pedido.deJSON(item))
}

async function apiAtualizarStatusPedido(id, status, tempoEstimado = null){
    const dados = await requisicao(`/api/pedidos/${id}/status`, {
        metodo: "PATCH",
        corpo: { status, tempoEstimado }
    })
    return Pedido.deJSON(dados)
}

async function apiBuscarCozinheiros(){
    const dados = await requisicao("/api/cozinheiros")
    return dados.map(item => Cozinheiro.deJSON(item))
}

async function apiAprovarCozinheiro(id){
    return await requisicao(`/api/cozinheiros/${id}/aprovar`, {
        metodo: "PATCH"
    })
}
