let perfilAtual = "CLIENTE"

function entrarComo(perfil) {
  perfilAtual = perfil
  sessionStorage.setItem("perfilAtual", perfil)

  if (perfil === "ADM") {
    window.location.href = "admin.html"
  } else if (perfil === "COZINHEIRO") {
    window.location.href = "cozinha.html"
  } else if (perfil === "CLIENTE") {
    window.location.href = "index.html"
  }
}

function verificarAcesso(perfilNecessario) {
  const perfil = sessionStorage.getItem("perfilAtual")

  if (perfil !== perfilNecessario) {
    alert("Acesso não autorizado!")
    window.location.href = "index.html"
  }
}
