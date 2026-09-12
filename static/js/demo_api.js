// Integração inicial via Fetch; as telas antigas continuam usando localStorage.
const formularioDemo = document.getElementById('pedido');
const mensagemDemo = document.getElementById('mensagem');
const enviarDemo = document.getElementById('enviar');

async function requisitarDemo(caminho, opcoes = {}) {
  const resposta = await fetch(caminho, opcoes);
  const corpo = await resposta.json();
  if (!resposta.ok) throw new Error(corpo.erro || 'Não foi possível concluir a operação.');
  return corpo.dados;
}

async function listarPedidosDemo() {
  const pedidos = await requisitarDemo('/api/pedidos');
  document.getElementById('resultado').textContent = JSON.stringify(pedidos, null, 2);
}

formularioDemo.addEventListener('submit', async (evento) => {
  evento.preventDefault();
  enviarDemo.disabled = true;
  mensagemDemo.textContent = 'Enviando pedido...';
  try {
    const campos = new FormData(formularioDemo);
    const pedido = await requisitarDemo('/api/pedidos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cliente: campos.get('cliente'),
        endereco: campos.get('endereco'),
        itens: [{ prato_id: Number(campos.get('prato')), quantidade: Number(campos.get('quantidade')) }]
      })
    });
    mensagemDemo.textContent = `Pedido #${pedido.id} criado. Total: R$ ${pedido.total.toFixed(2)}.`;
    try {
      await listarPedidosDemo();
    } catch (erro) {
      mensagemDemo.textContent += ' Não foi possível atualizar a lista; use Atualizar lista.';
    }
  } catch (erro) {
    mensagemDemo.textContent = erro.message;
  } finally {
    enviarDemo.disabled = false;
  }
});

document.getElementById('atualizar').addEventListener('click', async () => {
  try {
    await listarPedidosDemo();
    mensagemDemo.textContent = 'Lista atualizada.';
  } catch (erro) {
    mensagemDemo.textContent = erro.message;
  }
});

async function iniciarDemo() {
  mensagemDemo.textContent = 'Carregando cardápio...';
  try {
    const pratos = await requisitarDemo('/api/pratos');
    for (const prato of pratos) {
      const opcao = document.createElement('option');
      opcao.value = prato.id;
      opcao.textContent = `${prato.nome} — R$ ${prato.preco.toFixed(2)}`;
      document.getElementById('pratos').appendChild(opcao);
    }
    enviarDemo.disabled = pratos.length === 0;
    await listarPedidosDemo();
    mensagemDemo.textContent = 'Pronto para criar um pedido de teste.';
  } catch (erro) {
    mensagemDemo.textContent = erro.message;
  }
}

iniciarDemo();
