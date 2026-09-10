function toggleMenu(){
  document.getElementById('menuLateral').classList.toggle('aberto');
}

const dropdown = document.getElementById('dropdown');
const menuBtn = document.getElementById('menuBtn');
const menuList = document.getElementById('menuList');
const selected = document.getElementById('selected');

if (menuBtn && dropdown) {
  menuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.toggle('open');
  });
}

if (menuList) {
  menuList.querySelectorAll('button').forEach(item => {
    item.addEventListener('click', () => {
      const value = item.getAttribute('data-value');
      if (selected) selected.textContent = 'Selecionado: ' + value;
      if (dropdown) dropdown.classList.remove('open');
    });
  });
}

document.addEventListener('click', () => {
  if (dropdown) dropdown.classList.remove('open');
});
