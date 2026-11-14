const estado = {
    usuario: null,
    deveTrocarSenha: false,
    pratos: [],
    carrinho: new Carrinho(),
    pedidos: [],
    cozinheiros: [],
    temporizador: null
}

const TELA_DO_PERFIL = {
    CLIENTE: "cliente",
    COZINHEIRO: "cozinha",
    ADM: "admin"
}

const PAGINA_DO_PERFIL = {
    CLIENTE: "Cliente.html",
    COZINHEIRO: "Cozinheiro.html",
    ADM: "ADM.html"
}

const PAGINA_DE_LOGIN = {
    CLIENTE: "CadastroCliente.html",
    COZINHEIRO: "CadastroCozinheiro.html"
}

const STATUS_PEDIDO = {
    "Recebido": { rotulo: "Pedido recebido", classe: "aguardando" },
    "Em Preparo": { rotulo: "Em Preparo", classe: "preparo" },
    "Pronto": { rotulo: "Pronto para Entrega", classe: "pronto" },
    "Entregue": { rotulo: "Entregue", classe: "entregue" }
}

const INTERVALO_ATUALIZACAO = 5000

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
    const botao = criarElemento("button", texto, "btn-avancar-status")
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
    estado.deveTrocarSenha = false
    estado.pratos = []
    estado.pedidos = []
    estado.cozinheiros = []
    estado.carrinho.limparCarrinho()
    window.location.replace(document.body.dataset.login || "index.html")
}

async function iniciarSessao(resultado){
    estado.usuario = resultado.usuario
    estado.deveTrocarSenha = resultado.deveTrocarSenha

    const telaDoPerfil = TELA_DO_PERFIL[estado.usuario.perfil]
    if (document.body.dataset.pagina !== telaDoPerfil){
        window.location.replace(PAGINA_DO_PERFIL[estado.usuario.perfil])
        return
    }

    renderizarPerfil()
    atualizarBotoesDeSenha()
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
            iniciarAtualizacao()
            break
        default:
            throw new Error("Perfil de usuário inválido")
    }
}

function renderizarPerfil(){
    const usuario = estado.usuario
    document.querySelectorAll("[data-perfil]").forEach(elemento => {
        elemento.textContent = usuario[elemento.dataset.perfil] ?? "—"
    })
    const endereco = campo("pedido-endereco")
    if (endereco !== null){
        endereco.placeholder = usuario.endereco ?? ""
    }
}

function atualizarBotoesDeSenha(){
    document.querySelectorAll("[data-oculto-na-troca]").forEach(botao => {
        botao.hidden = estado.deveTrocarSenha
    })
}

function iniciarAtualizacao(){
    clearInterval(estado.temporizador)
    estado.temporizador = setInterval(atualizarSilenciosamente, INTERVALO_ATUALIZACAO)
}

async function atualizarSilenciosamente(){
    if (document.hidden || estado.usuario === null){
        return
    }
    const listas = ["lista-fila", "lista-prontos"].map(campo).filter(lista => lista !== null)
    if (listas.some(lista => lista.contains(document.activeElement))){
        return
    }
    try{
        if (estado.usuario.perfil === "ADM"){
            await carregarCozinheiros()
        } else {
            await carregarPedidos()
        }
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
        estado.deveTrocarSenha = false
        atualizarBotoesDeSenha()
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
    const cartao = criarElemento("div", "", "item-cardapio")
    const info = criarElemento("div")
    const preco = criarElemento("p")
    preco.append(criarElemento("strong", formatarPreco(prato.preco)))
    info.append(criarElemento("h3", prato.nome), criarElemento("p", prato.descricao), preco)

    const acoes = criarElemento("div", "", "acoes-item")
    acoes.append(criarBotao("Adicionar ao Carrinho", "adicionar", prato.id))

    cartao.append(info, acoes)
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
        const linha = criarElemento("div", "", "item-carrinho")
        const nome = criarElemento("p")
        nome.append(criarElemento("strong", item.nome))
        linha.append(
            nome,
            criarElemento("p", `Qtd: ${item.quantidade} x ${formatarPreco(item.preco)} = Subtotal: ${formatarPreco(item.subtotal)}`),
            criarBotao("Remover 1 unidade", "menos", item.id),
            criarBotao("Adicionar 1", "mais", item.id),
            criarBotao("Remover item", "remover", item.id)
        )
        return linha
    })
    if (linhas.length === 0){
        linhas.push(criarElemento("p", "Seu carrinho está vazio.", "fila-vazia"))
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
        mostrarSucesso(`Pedido #${criado.id} realizado com sucesso!`)
    })
}

async function carregarPedidos(){
    const pedidos = await apiBuscarPedidos()
    if (estado.usuario === null){
        return
    }
    estado.pedidos = pedidos
    if (estado.usuario.perfil === "COZINHEIRO"){
        renderizarFila()
    } else {
        renderizarMeusPedidos()
    }
}

function criarCartaoMeuPedido(pedido){
    const cartao = criarElemento("div", "", `kds-cartao ${STATUS_PEDIDO[pedido.status].classe}`)

    const topo = criarElemento("div", "", "linha-pedido-topo")
    topo.append(criarElemento("span", `Pedido #${pedido.id}`, "pedido-numero"))

    const itens = criarElemento("ul", "", "pedido-itens-lista")
    pedido.itens.forEach(item => {
        itens.append(criarElemento("li", `${item.quantidade}x ${item.nome}`))
    })

    cartao.append(topo, itens)
    if (pedido.tempoEstimado){
        const tempo = criarElemento("span", "Tempo estimado: ", "pedido-tempo")
        tempo.append(criarElemento("strong", `${pedido.tempoEstimado} min`))
        cartao.append(tempo)
    }
    cartao.append(criarElemento("span", `Total: ${formatarPreco(pedido.total)}`, "pedido-tempo"))
    return cartao
}

function renderizarMeusPedidos(){
    const ordenados = [...estado.pedidos].sort((a, b) => a.id - b.id)

    Object.entries(STATUS_PEDIDO).forEach(([status, info]) => {
        const doStatus = ordenados.filter(pedido => pedido.status === status)
        campo(`kds-col-${info.classe}`).replaceChildren(...doStatus.map(criarCartaoMeuPedido))
        campo(`kds-count-${info.classe}`).textContent = doStatus.length
    })

    campo("meus-pedidos-vazio").hidden = ordenados.length !== 0
    campo("total-pedidos").textContent = ordenados.length
}

function criarCartaoPedido(pedido){
    const info = STATUS_PEDIDO[pedido.status]
    const cartao = criarElemento("div", "", `linha-pedido-cozinha ${info.classe}`)

    const dados = criarElemento("div", "", "info-pedido-cozinha")
    const topo = criarElemento("div", "", "linha-pedido-topo")
    topo.append(
        criarElemento("span", `Pedido #${pedido.id} - ${pedido.nomeCliente}`, "pedido-numero"),
        criarElemento("span", info.rotulo, `status-badge ${info.classe}`)
    )
    const itens = criarElemento("ul", "", "pedido-itens-lista")
    pedido.itens.forEach(item => {
        itens.append(criarElemento("li", `${item.quantidade}x ${item.nome}`))
    })
    const tempo = pedido.tempoEstimado ? ` · tempo estimado: ${pedido.tempoEstimado} min` : ""
    dados.append(topo, itens, criarElemento("span", `Endereço: ${pedido.endereco}${tempo}`, "pedido-tempo"))

    const acoes = criarElemento("div", "", "acoes-pedido-cozinha")
    if (pedido.status === "Recebido"){
        const minutos = criarElemento("input", "", "campo-minutos")
        minutos.type = "number"
        minutos.min = 1
        minutos.max = 240
        minutos.id = `minutos-${pedido.id}`
        minutos.placeholder = "Minutos"
        acoes.append(minutos, criarBotao("Iniciar Preparo", "iniciar", pedido.id))
    } else if (pedido.status === "Em Preparo"){
        acoes.append(criarBotao("Marcar como Pronto", "pronto", pedido.id))
    } else if (pedido.status === "Pronto"){
        acoes.append(criarBotao("Marcar como Entregue", "entregue", pedido.id))
    }

    cartao.append(dados, acoes)
    return cartao
}

function renderizarFila(){
    const rascunhos = new Map()
    document.querySelectorAll("input[id^='minutos-']").forEach(input => {
        rascunhos.set(input.id, input.value)
    })

    const ordenados = [...estado.pedidos].sort((a, b) => a.id - b.id)
    const naFila = ordenados.filter(pedido => pedido.naFila)
    const prontos = ordenados.filter(pedido => pedido.pronto)

    const vazioFila = criarElemento("p", "Nenhum pedido na fila.", "fila-vazia")
    const vazioProntos = criarElemento("p", "Nenhum pedido pronto no momento.", "fila-vazia")

    campo("lista-fila").replaceChildren(...(naFila.length ? naFila.map(criarCartaoPedido) : [vazioFila]))
    campo("lista-prontos").replaceChildren(...(prontos.length ? prontos.map(criarCartaoPedido) : [vazioProntos]))

    document.querySelectorAll("input[id^='minutos-']").forEach(input => {
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
        const cartao = criarElemento("div", "", "item-cardapio")
        const situacao = prato.ativo ? "Ativo" : "Inativo"

        const info = criarElemento("div")
        const detalhes = criarElemento("p")
        detalhes.append(criarElemento("strong", formatarPreco(prato.preco)), ` · ${prato.categoria} · ${situacao}`)
        info.append(criarElemento("h3", prato.nome), criarElemento("p", prato.descricao), detalhes)

        const acoes = criarElemento("div", "", "acoes-item")
        acoes.append(
            criarBotao("Editar", "editar", prato.id),
            criarBotao(prato.ativo ? "Inativar" : "Ativar", "alternar", prato.id),
            criarBotao("Remover", "remover", prato.id)
        )

        cartao.append(info, acoes)
        return cartao
    })
    campo("lista-admin-pratos").replaceChildren(...cartoes)
}

function limparFormularioPrato(){
    campo("form-prato").reset()
    campo("prato-id").value = ""
    campo("titulo-form-prato").textContent = "Cadastrar prato"
}

function editarPrato(idPrato){
    const prato = estado.pratos.find(item => item.id === idPrato)
    campo("prato-id").value = prato.id
    campo("prato-nome").value = prato.nome
    campo("prato-descricao").value = prato.descricao
    campo("prato-preco").value = prato.preco
    campo("prato-categoria").value = prato.categoria
    campo("prato-ativo").checked = prato.ativo
    campo("titulo-form-prato").textContent = "Editar prato selecionado"
    campo("form-prato").scrollIntoView({ behavior: "smooth", block: "center" })
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
    campo("total-solicitacoes").textContent = ordenados.filter(cozinheiro => !cozinheiro.ativo).length

    const linhas = ordenados.map(cozinheiro => {
        const situacao = cozinheiro.ativo ? "Aprovado" : "Pendente"
        const linha = criarElemento("div", "", "linha-solicitacao")

        const info = criarElemento("div", "", "info-solicitacao")
        info.append(
            criarElemento("strong", cozinheiro.nome),
            criarElemento("span", `${cozinheiro.email} · Turno: ${cozinheiro.turno} · Especialidade: ${cozinheiro.especialidade}`),
            criarElemento("span", `Situação: ${situacao}`)
        )
        linha.append(info)

        if (!cozinheiro.ativo){
            const acoes = criarElemento("div", "", "acoes-item")
            acoes.append(
                criarBotao("Aprovar", "aprovar", cozinheiro.id),
                criarBotao("Recusar", "recusar", cozinheiro.id)
            )
            linha.append(acoes)
        }
        return linha
    })
    if (linhas.length === 0){
        linhas.push(criarElemento("p", "Nenhum cozinheiro cadastrado.", "sem-solicitacoes"))
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

async function recusarCozinheiro(idCozinheiro){
    const cozinheiro = estado.cozinheiros.find(item => item.id === idCozinheiro)
    if (!confirm(`Recusar o cadastro de ${cozinheiro.nome}?`)){
        return
    }
    await executarAcao(async () => {
        await apiRecusarCozinheiro(idCozinheiro)
        await carregarCozinheiros()
        mostrarSucesso(`Cadastro de ${cozinheiro.nome} recusado`)
    })
}

function mostrarSenhaProvisoria(nome, senha){
    fecharSenhaProvisoria()

    const caixa = criarElemento("div", "", "aviso-senha")
    caixa.id = "aviso-senha"

    const titulo = criarElemento("p", `Senha provisória de ${nome}: `)
    titulo.append(criarElemento("strong", senha))

    const copiar = criarElemento("button", "Copiar", "btn-avancar-status")
    copiar.type = "button"
    copiar.addEventListener("click", async () => {
        try{
            await navigator.clipboard.writeText(senha)
            mostrarSucesso("Senha copiada")
        } catch (erro){
            mostrarErro("Não foi possível copiar. Copie manualmente.")
        }
    })

    const fechar = criarElemento("button", "Fechar", "btn-avancar-status")
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

function ligar(idElemento, evento, funcao){
    const elemento = campo(idElemento)
    if (elemento !== null){
        elemento.addEventListener(evento, funcao)
    }
}

function tratarCliques(idContainer, acoes){
    const container = campo(idContainer)
    if (container === null){
        return
    }
    container.addEventListener("click", evento => {
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

function preencherOpcoes(idSelect, opcoes){
    const select = campo(idSelect)
    if (select === null || select.options.length > 0){
        return
    }
    select.append(new Option("Selecione...", ""))
    opcoes.forEach(opcao => select.append(new Option(opcao, opcao)))
}

function registrarEventos(){
    ligar("form-login", "submit", fazerLogin)
    ligar("form-cadastro-cliente", "submit", cadastrarCliente)
    ligar("form-cadastro-cozinheiro", "submit", cadastrarCozinheiro)
    ligar("form-troca-senha", "submit", trocarSenha)
    ligar("form-prato", "submit", salvarPrato)
    ligar("btn-cancelar-prato", "click", limparFormularioPrato)
    ligar("btn-finalizar", "click", finalizarPedido)

    preencherOpcoes("coz-turno", TURNOS)
    preencherOpcoes("coz-especialidade", ESPECIALIDADES)

    document.querySelectorAll("[data-logout]").forEach(botao => {
        botao.addEventListener("click", fazerLogout)
    })
    document.querySelectorAll("[data-ir]").forEach(botao => {
        botao.addEventListener("click", () => {
            limparMensagem()
            mostrarTela(botao.dataset.ir)
        })
    })
    document.querySelectorAll("[data-entrar-como]").forEach(botao => {
        botao.addEventListener("click", () => {
            window.location.href = PAGINA_DE_LOGIN[botao.dataset.entrarComo]
        })
    })

    tratarCliques("lista-cardapio", { adicionar: adicionarAoCarrinho })
    tratarCliques("lista-carrinho", { mais: adicionarAoCarrinho, menos: diminuirDoCarrinho, remover: removerDoCarrinho })
    tratarCliques("lista-fila", { iniciar: avancarPedido, pronto: avancarPedido })
    tratarCliques("lista-prontos", { entregue: avancarPedido })
    tratarCliques("lista-admin-pratos", { editar: editarPrato, alternar: alternarPrato, remover: removerPrato })
    tratarCliques("lista-cozinheiros", { aprovar: aprovarCozinheiro, recusar: recusarCozinheiro })
}

async function inicializar(){
    registrarEventos()
    if (document.querySelector("[data-tela]") === null){
        return
    }
    if (campo("form-login") !== null){
        mostrarTela("login")
    }

    let resultado
    try{
        resultado = await apiUsuarioAtual()
    } catch (erro){
        if (erro.status !== 401){
            mostrarErro(erro.message)
        } else if (document.body.dataset.login){
            window.location.replace(document.body.dataset.login)
        }
        return
    }
    await executarAcao(() => iniciarSessao(resultado))
}

document.addEventListener("DOMContentLoaded", inicializar)
