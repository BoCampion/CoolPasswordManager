const openModalButtons = document.querySelectorAll('[data-modal-target]');
const closeModalButtons = document.querySelectorAll('[data-close-button]');
const overlay = document.getElementById('overlay');
const characters ='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789123456789!@#$%^&*()_';

openModalButtons.forEach(button => {
  button.addEventListener('click', () => {
    const modal = document.querySelector(button.dataset.modalTarget);
    openModal(modal);
  });
});

overlay.addEventListener('click', () => {
  const modals = document.querySelectorAll('.modal.active');
  modals.forEach(modal => {
    closeModal(modal);
  });
});

closeModalButtons.forEach(button => {
  button.addEventListener('click', () => {
    const modal = button.closest('.modal');
    closeModal(modal);
  });
});

function openModal(modal) {
  if (!modal) return;
  modal.classList.add('active');
  overlay.classList.add('active');
}

function closeModal(modal) {
  if (!modal) return;
  modal.classList.remove('active');
  overlay.classList.remove('active');
}


function Look_at_yo_shit(index, button) {
    const passwordElement = document.getElementById(`password${index}`);
    const actualPassword = passwordElement.getAttribute("data-password");
    
    if (passwordElement.innerText === "********") {

        passwordElement.innerText = actualPassword;
        button.innerText = "hide";
    } else {
        passwordElement.innerText = "********";
        button.innerText = "show";
    }
  }

function makelongthing(length) {
  let result = ' ';
  const charactersLength = characters.length;
  for ( let i = 0; i < length; i++ ) {
      result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }

  return result;
}
function cool_password(){
  document.getElementById("password").value = makelongthing(20)
}
