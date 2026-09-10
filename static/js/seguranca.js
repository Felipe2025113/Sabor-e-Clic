let perfilAtual = sessionStorage.getItem("perfilAtual") || "CLIENTE"

function entrarComo(perfil) {
  perfilAtual = perfil
  sessionStorage.setItem("perfilAtual", perfil)

  if (perfil === "ADM") {
    window.location.href = "/templates/ADM.html"
  } else if (perfil === "COZINHEIRO") {
    window.location.href = "/templates/Cozinheiro.html"
  } else if (perfil === "CLIENTE") {
    window.location.href = "/templates/Cliente.html"
  }
}

function verificarAcesso(perfilNecessario) {
  const perfil = sessionStorage.getItem("perfilAtual")

  if (perfil !== perfilNecessario) {
    alert("Acesso não autorizado")
    window.location.href = "/templates/index.html"
  }
}

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-entrar-como]").forEach(function (botao) {
    botao.addEventListener("click", function () {
      entrarComo(botao.getAttribute("data-entrar-como"))
    })
  })
})
