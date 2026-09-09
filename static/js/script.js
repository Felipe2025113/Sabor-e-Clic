const dropdown = document.getElementById('dropdown');
const menuBtn = document.getElementById('menuBtn');
const menuList = document.getElementById('menuList');
const selected = document.getElementById('selected');


function toggleMenu(){
    document.getElementById('menuLateral').classList.toggle('aberto');
}

menuBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  dropdown.classList.toggle('open');
});

menuList.querySelectorAll('button').forEach(item => {
  item.addEventListener('click', () => {
    const value = item.getAttribute('data-value');
    selected.textContent = 'Selecionado: ' + value;
    dropdown.classList.remove('open');
  });
});

document.addEventListener('click', () => {
  dropdown.classList.remove('open');
});