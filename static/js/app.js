const estado = {
    usuario: null,
    pratos: [],
    carrinho: new Carrinho(),
    pedidos: [],
    cozinheiros: [],
    temporizador: null
}

const campo = id => document.getElementById(id)

function mostrarLoading(){
    campo("loading").hidden = false
}
function esconderLoading(){
    campo("loading").hidden = true
}

function mostrarErro(mensagem){
    campo("mensagem").textContent = mensagem
    campo("mensagem").className = "mensagem erro"
}
function mostrarSucesso(mensagem){
    campo("mensagem").textContent = mensagem
    campo("mensagem").className = "mensagem sucesso"
}

function limparMensagem(){
    campo("mensagem").textContent = ""
}

function mostrarTela(nome){
    document.querySelectorAll("[data-tela]").forEach(secao => {
        secao.hidden = secao.dataset.tela !== nome
    })
}

function formatarPreco(valor){
    return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

function criarElemento(tag, texto = "", classe = ""){
    const elemento = document.createElement(tag)
    elemento.textContent = texto
    if (classe){
        elemento.className = classe
    }
    return elemento
}

function criarBotao(texto, acao, id){
    const botao = criarElemento("button", texto)
    botao.type = "button"
    botao.dataset.acao = acao
    botao.dataset.id = id
    return botao
}

function descreverItens(pedido){
    return pedido.itens.map(item => `${item.quantidade}x ${item.nome}`).join(", ")
}

async function executarAcao(acao){
    limparMensagem()
    mostrarLoading()
    try{
        await acao()
    } catch (erro){
        if (erro.status === 401 && estado.usuario !== null){
            encerrarSessaoLocal()
        }
        mostrarErro(erro.message)
    } finally{
        esconderLoading()
    }
}

function executarLocal(acao){
    try{
        acao()
        if (campo("mensagem").classList.contains("erro")){
            limparMensagem()
        }
    } catch (erro){
        mostrarErro(erro.message)
    }
}

function encerrarSessaoLocal(){
    clearInterval(estado.temporizador)
    estado.temporizador = null
    estado.usuario = null
    estado.pratos = []
    estado.pedidos = []
    estado.cozinheiros = []
    estado.carrinho.limparCarrinho()
    fecharSenhaProvisoria()
    mostrarTela("login")
}

async function iniciarSessao(resultado){
    estado.usuario = resultado.usuario
    if (resultado.deveTrocarSenha){
        mostrarTela("troca-senha")
        return
    }
    await abrirTelaDoPerfil()
}

async function abrirTelaDoPerfil(){
    switch (estado.usuario.perfil){
        case "CLIENTE":
            mostrarTela("cliente")
            renderizarCarrinho()
            await carregarCardapio()
            await carregarPedidos()
            iniciarAtualizacao()
            break
        case "COZINHEIRO":
            mostrarTela("cozinha")
            await carregarPedidos()
            iniciarAtualizacao()
            break
        case "ADM":
            mostrarTela("admin")
            await carregarCardapio()
            await carregarCozinheiros()
            break
        default:
            throw new Error("Perfil de usuário inválido")
    }
}

function iniciarAtualizacao(){
    clearInterval(estado.temporizador)
    estado.temporizador = setInterval(atualizarPedidosSilencioso, 15000)
}

async function atualizarPedidosSilencioso(){
    if (document.hidden || estado.usuario === null){
        return
    }
    const fila = campo("lista-fila")
    if (fila.contains(document.activeElement)){
        return
    }
    try{
        await carregarPedidos()
    } catch (erro){
        if (erro.status === 401){
            encerrarSessaoLocal()
        }
    }
}

async function fazerLogin(evento){
    evento.preventDefault()
    await executarAcao(async () => {
        const login = new Login(campo("login-email").value, campo("login-senha").value)
        const resultado = await apiLogin(login)
        campo("form-login").reset()
        await iniciarSessao(resultado)
    })
}

async function fazerLogout(){
    await executarAcao(async () => {
        try{
            await apiLogout()
        } finally{
            encerrarSessaoLocal()
        }
    })
}

async function trocarSenha(evento){
    evento.preventDefault()
    await executarAcao(async () => {
        const troca = new AlterarSenha(
            campo("senha-atual").value,
            campo("senha-nova").value,
            campo("senha-confirmacao").value
        )
        await apiAlterarSenha(troca)
        campo("form-troca-senha").reset()
        await abrirTelaDoPerfil()
        mostrarSucesso("Senha alterada com sucesso")
    })
}

async function cadastrarCliente(evento){
    evento.preventDefault()
    await executarAcao(async () => {
        const cadastro = new CadastroCliente(
            campo("cli-nome").value,
            campo("cli-email").value,
            campo("cli-senha").value,
            campo("cli-endereco").value
        )
        await apiCadastrarCliente(cadastro)
        campo("form-cadastro-cliente").reset()
        mostrarTela("login")
        mostrarSucesso("Cadastro realizado! Faça login para continuar.")
    })
}

async function cadastrarCozinheiro(evento){
    evento.preventDefault()
    await executarAcao(async () => {
        const cadastro = new CadastroCozinheiro(
            campo("coz-nome").value,
            campo("coz-email").value,
            campo("coz-turno").value,
            campo("coz-especialidade").value
        )
        await apiCadastrarCozinheiro(cadastro)
        campo("form-cadastro-cozinheiro").reset()
        mostrarTela("login")
        mostrarSucesso("Cadastro enviado! Aguarde a análise do administrador.")
    })
}

async function carregarCardapio(){
    estado.pratos = await apiBuscarPratos()
    if (estado.usuario.perfil === "ADM"){
        renderizarCardapioAdmin()
    } else {
        renderizarCardapioCliente()
    }
}

function criarCartaoPrato(prato){
    const cartao = criarElemento("article", "", "cartao-prato")
    cartao.append(
        criarElemento("h3", prato.nome),
        criarElemento("p", prato.descricao),
        criarElemento("p", prato.categoria),
        criarElemento("strong", formatarPreco(prato.preco)),
        criarBotao("Adicionar", "adicionar", prato.id)
    )
    return cartao
}

function renderizarCardapioCliente(){
    const ativos = estado.pratos.filter(prato => prato.ativo)
    campo("lista-cardapio").replaceChildren(...ativos.map(criarCartaoPrato))
}

function adicionarAoCarrinho(idPrato){
    executarLocal(() => {
        const prato = estado.pratos.find(item => item.id === idPrato)
        estado.carrinho.adicionarItem(ItemPedido.dePrato(prato))
        renderizarCarrinho()
    })
}

function diminuirDoCarrinho(idItem){
    executarLocal(() => {
        estado.carrinho.diminuirQuantidade(idItem)
        renderizarCarrinho()
    })
}

function removerDoCarrinho(idItem){
    executarLocal(() => {
        estado.carrinho.removerItem(idItem)
        renderizarCarrinho()
    })
}

function renderizarCarrinho(){
    const itens = estado.carrinho.itens
    const linhas = itens.map(item => {
        const linha = criarElemento("li", `${item.nome} x${item.quantidade} - ${formatarPreco(item.subtotal)} `)
        linha.append(
            criarBotao("-", "menos", item.id),
            criarBotao("+", "mais", item.id),
            criarBotao("Remover", "remover", item.id)
        )
        return linha
    })
    if (linhas.length === 0){
        linhas.push(criarElemento("li", "Seu carrinho está vazio"))
    }
    campo("lista-carrinho").replaceChildren(...linhas)
    campo("total-carrinho").textContent = formatarPreco(estado.carrinho.total)
    campo("btn-finalizar").disabled = itens.length === 0
}

async function finalizarPedido(){
    await executarAcao(async () => {
        const endereco = campo("pedido-endereco").value.trim()
        const pedido = Pedido.doCarrinho(estado.carrinho, estado.usuario, endereco)
        const criado = await apiCriarPedido(pedido)
        estado.carrinho.limparCarrinho()
        campo("pedido-endereco").value = ""
        renderizarCarrinho()
        await carregarPedidos()
        mostrarSucesso(`Pedido #${criado.id} recebido!`)
    })
}

async function carregarPedidos(){
    const pedidos = await apiBuscarPedidos()
    if (estado.usuario === null){
        return
    }
    estado.pedidos = pedidos
    renderizarPedidos()
}

function renderizarPedidos(){
    if (estado.usuario.perfil === "COZINHEIRO"){
        renderizarFila()
    } else {
        renderizarMeusPedidos()
    }
}

function renderizarMeusPedidos(){
    const ordenados = [...estado.pedidos].sort((a, b) => b.id - a.id)
    const linhas = ordenados.map(pedido => {
        const previsao = pedido.status === "Em Preparo" ? ` - previsão de ${pedido.tempoEstimado} min` : ""
        const texto = `#${pedido.id} - ${pedido.status}${previsao} - ${descreverItens(pedido)} - ${formatarPreco(pedido.total)}`
        return criarElemento("li", texto)
    })
    campo("lista-meus-pedidos").replaceChildren(...linhas)
}

function criarCartaoPedido(pedido){
    const cartao = criarElemento("article", "", "cartao-pedido")
    cartao.append(
        criarElemento("h3", `Pedido #${pedido.id} - ${pedido.status}`),
        criarElemento("p", `${pedido.nomeCliente} - ${pedido.endereco}`),
        criarElemento("p", descreverItens(pedido))
    )
    if (pedido.status === "Recebido"){
        const minutos = criarElemento("input")
        minutos.type = "number"
        minutos.min = 1
        minutos.max = 240
        minutos.id = `minutos-${pedido.id}`
        minutos.placeholder = "Minutos"
        cartao.append(minutos, criarBotao("Iniciar preparo", "iniciar", pedido.id))
    } else if (pedido.status === "Em Preparo"){
        cartao.append(
            criarElemento("p", `Previsão: ${pedido.tempoEstimado} min`),
            criarBotao("Marcar pronto", "pronto", pedido.id)
        )
    } else if (pedido.status === "Pronto"){
        cartao.append(criarBotao("Marcar entregue", "entregue", pedido.id))
    }
    return cartao
}

function renderizarFila(){
    const lista = campo("lista-fila")
    const rascunhos = new Map()
    lista.querySelectorAll("input[id^='minutos-']").forEach(input => {
        rascunhos.set(input.id, input.value)
    })

    const fila = estado.pedidos
        .filter(pedido => pedido.naFila || pedido.pronto)
        .sort((a, b) => a.id - b.id)
    lista.replaceChildren(...fila.map(criarCartaoPedido))

    lista.querySelectorAll("input[id^='minutos-']").forEach(input => {
        if (rascunhos.has(input.id)){
            input.value = rascunhos.get(input.id)
        }
    })
}

async function avancarPedido(idPedido, acao){
    await executarAcao(async () => {
        const original = estado.pedidos.find(item => item.id === idPedido)
        const pedido = Pedido.deJSON(original.toJSON())
        if (acao === "iniciar"){
            pedido.iniciarPreparo(campo(`minutos-${idPedido}`).value)
        } else if (acao === "pronto"){
            pedido.marcarPronto()
        } else {
            pedido.marcarEntregue()
        }
        await apiAtualizarStatusPedido(pedido.id, pedido.status, pedido.tempoEstimado)
        await carregarPedidos()
    })
}

function renderizarCardapioAdmin(){
    const cartoes = estado.pratos.map(prato => {
        const cartao = criarElemento("article", "", "cartao-prato")
        const situacao = prato.ativo ? "Ativo" : "Inativo"
        cartao.append(
            criarElemento("h3", prato.nome),
            criarElemento("p", `${prato.categoria} - ${formatarPreco(prato.preco)} - ${situacao}`),
            criarBotao("Editar", "editar", prato.id),
            criarBotao(prato.ativo ? "Inativar" : "Ativar", "alternar", prato.id),
            criarBotao("Remover", "remover", prato.id)
        )
        return cartao
    })
    campo("lista-admin-pratos").replaceChildren(...cartoes)
}

function limparFormularioPrato(){
    campo("form-prato").reset()
    campo("prato-id").value = ""
}

function editarPrato(idPrato){
    const prato = estado.pratos.find(item => item.id === idPrato)
    campo("prato-id").value = prato.id
    campo("prato-nome").value = prato.nome
    campo("prato-descricao").value = prato.descricao
    campo("prato-preco").value = prato.preco
    campo("prato-categoria").value = prato.categoria
    campo("prato-ativo").checked = prato.ativo
}

async function salvarPrato(evento){
    evento.preventDefault()
    await executarAcao(async () => {
        const id = campo("prato-id").value ? Number(campo("prato-id").value) : null
        const prato = new Prato({
            id,
            nome: campo("prato-nome").value,
            descricao: campo("prato-descricao").value,
            preco: campo("prato-preco").value,
            categoria: campo("prato-categoria").value,
            ativo: campo("prato-ativo").checked
        })
        if (id === null){
            await apiCriarPrato(prato)
        } else {
            await apiAtualizarPrato(id, prato)
        }
        limparFormularioPrato()
        await carregarCardapio()
        mostrarSucesso("Prato salvo com sucesso")
    })
}

async function alternarPrato(idPrato){
    await executarAcao(async () => {
        const original = estado.pratos.find(item => item.id === idPrato)
        const prato = Prato.deJSON(original.toJSON())
        if (prato.ativo){
            prato.inativar()
        } else {
            prato.ativar()
        }
        await apiAtualizarPrato(idPrato, prato)
        await carregarCardapio()
    })
}

async function removerPrato(idPrato){
    if (!confirm("Deseja remover este prato do cardápio?")){
        return
    }
    await executarAcao(async () => {
        await apiRemoverPrato(idPrato)
        await carregarCardapio()
        mostrarSucesso("Prato removido")
    })
}

async function carregarCozinheiros(){
    estado.cozinheiros = await apiBuscarCozinheiros()
    renderizarCozinheiros()
}

function renderizarCozinheiros(){
    const ordenados = [...estado.cozinheiros].sort((a, b) => Number(a.ativo) - Number(b.ativo))
    const linhas = ordenados.map(cozinheiro => {
        const situacao = cozinheiro.ativo ? "Aprovado" : "Pendente"
        const texto = `${cozinheiro.nome} - ${cozinheiro.email} - ${cozinheiro.turno} - ${cozinheiro.especialidade} - ${situacao} `
        const linha = criarElemento("li", texto)
        if (!cozinheiro.ativo){
            linha.append(criarBotao("Aprovar", "aprovar", cozinheiro.id))
        }
        return linha
    })
    if (linhas.length === 0){
        linhas.push(criarElemento("li", "Nenhum cozinheiro cadastrado"))
    }
    campo("lista-cozinheiros").replaceChildren(...linhas)
}

async function aprovarCozinheiro(idCozinheiro){
    await executarAcao(async () => {
        const cozinheiro = estado.cozinheiros.find(item => item.id === idCozinheiro)
        const resposta = await apiAprovarCozinheiro(idCozinheiro)
        await carregarCozinheiros()
        mostrarSenhaProvisoria(cozinheiro.nome, resposta.senhaProvisoria)
        mostrarSucesso(`${cozinheiro.nome} aprovado`)
    })
}

function mostrarSenhaProvisoria(nome, senha){
    fecharSenhaProvisoria()

    const caixa = criarElemento("div", "", "aviso-senha")
    caixa.id = "aviso-senha"

    const titulo = criarElemento("p", `Senha provisória de ${nome}: `)
    titulo.append(criarElemento("strong", senha))

    const copiar = criarElemento("button", "Copiar")
    copiar.type = "button"
    copiar.addEventListener("click", async () => {
        try{
            await navigator.clipboard.writeText(senha)
            mostrarSucesso("Senha copiada")
        } catch (erro){
            mostrarErro("Não foi possível copiar. Copie manualmente.")
        }
    })

    const fechar = criarElemento("button", "Fechar")
    fechar.type = "button"
    fechar.addEventListener("click", fecharSenhaProvisoria)

    caixa.append(
        titulo,
        criarElemento("p", "Repasse ao cozinheiro. Ela não será exibida novamente."),
        copiar,
        fechar
    )
    campo("lista-cozinheiros").before(caixa)
}

function fecharSenhaProvisoria(){
    const caixa = document.getElementById("aviso-senha")
    if (caixa){
        caixa.remove()
    }
}

function tratarCliques(idContainer, acoes){
    campo(idContainer).addEventListener("click", evento => {
        const botao = evento.target.closest("button[data-acao]")
        if (!botao){
            return
        }
        const funcao = acoes[botao.dataset.acao]
        if (funcao){
            funcao(Number(botao.dataset.id), botao.dataset.acao)
        }
    })
}

function registrarEventos(){
    campo("form-login").addEventListener("submit", fazerLogin)
    campo("form-cadastro-cliente").addEventListener("submit", cadastrarCliente)
    campo("form-cadastro-cozinheiro").addEventListener("submit", cadastrarCozinheiro)
    campo("form-troca-senha").addEventListener("submit", trocarSenha)
    campo("form-prato").addEventListener("submit", salvarPrato)
    campo("btn-cancelar-prato").addEventListener("click", limparFormularioPrato)
    campo("btn-finalizar").addEventListener("click", finalizarPedido)

    document.querySelectorAll("[data-logout]").forEach(botao => {
        botao.addEventListener("click", fazerLogout)
    })
    document.querySelectorAll("[data-ir]").forEach(botao => {
        botao.addEventListener("click", () => {
            limparMensagem()
            mostrarTela(botao.dataset.ir)
        })
    })

    tratarCliques("lista-cardapio", { adicionar: adicionarAoCarrinho })
    tratarCliques("lista-carrinho", { mais: adicionarAoCarrinho, menos: diminuirDoCarrinho, remover: removerDoCarrinho })
    tratarCliques("lista-fila", { iniciar: avancarPedido, pronto: avancarPedido, entregue: avancarPedido })
    tratarCliques("lista-admin-pratos", { editar: editarPrato, alternar: alternarPrato, remover: removerPrato })
    tratarCliques("lista-cozinheiros", { aprovar: aprovarCozinheiro })
}

async function inicializar(){
    registrarEventos()
    mostrarTela("login")
    let resultado
    try{
        resultado = await apiUsuarioAtual()
    } catch (erro){
        if (erro.status !== 401){
            mostrarErro(erro.message)
        }
        return
    }
    await executarAcao(() => iniciarSessao(resultado))
}

document.addEventListener("DOMContentLoaded", inicializar)
