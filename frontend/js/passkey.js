"use strict";
const feedback = document.getElementById('feedback');
document.getElementById('create-passkey').addEventListener('click', () => {
  feedback.textContent = 'Demo only: passkey creation requires Django WebAuthn registration and server verification. No passkey was created.';
});
document.getElementById('skip-passkey').addEventListener('click', () => {
  window.location.href = './role.html';
});
