 'use strict';

const carousel = document.querySelector('.carousel');
const track = document.getElementById('slides');
const slides = [...document.querySelectorAll('.slide')];
const dots = [...document.querySelectorAll('.dot')];
const skip = document.getElementById('skip');
let current = 0;
let touchStartX = null;
let touchStartY = null;

function goToSlide(index) {
  current = Math.max(0, Math.min(index, slides.length - 1));
  track.style.transform = `translateX(-${current * 100}%)`;
  slides.forEach((slide, i) => {
    slide.inert = i !== current;
    slide.setAttribute('aria-hidden', String(i !== current));
  });
  dots.forEach((dot, i) => {
    dot.classList.toggle('active', i === current);
    if (i === current) dot.setAttribute('aria-current', 'true');
    else dot.removeAttribute('aria-current');
  });
  skip.textContent = current === slides.length - 1 ? 'Done' : 'Skip';
}

dots.forEach(dot => dot.addEventListener('click', () => goToSlide(Number(dot.dataset.slide))));
skip.addEventListener('click', () => {
  if (current !== slides.length - 1) goToSlide(slides.length - 1);
  else window.location.href = './phone.html';
});
carousel.addEventListener('touchstart', e => {
  touchStartX = e.changedTouches[0].screenX;
  touchStartY = e.changedTouches[0].screenY;
}, {passive:true});
carousel.addEventListener('touchend', e => {
  if (touchStartX === null) return;
  const dx = e.changedTouches[0].screenX - touchStartX;
  const dy = e.changedTouches[0].screenY - touchStartY;
  if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy)) goToSlide(current + (dx < 0 ? 1 : -1));
  touchStartX = touchStartY = null;
}, {passive:true});
carousel.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight') {e.preventDefault();goToSlide(current + 1);}
  if (e.key === 'ArrowLeft') {e.preventDefault();goToSlide(current - 1);}
});

const dialog = document.getElementById('notice');
const title = document.getElementById('notice-title');
const message = document.getElementById('notice-text');
const messages = {
  finish: ['Welcome to MoveGo', 'The next authentication screen has not been built yet.'],
  google: ['Google sign-in', 'Django Google authentication is not connected yet.'],
  passkey: ['Passkey sign-in', 'Passkey registration and sign-in are not connected yet.'],
  phone: ['Phone sign-in', 'Opening phone verification…'],
  terms: ['Terms of Use', 'The Terms of Use page has not been added yet.'],
  privacy: ['Privacy Policy', 'The Privacy Policy page has not been added yet.']
};
function showNotice(feature) {
  const content = messages[feature];
  if (!content) return;
  title.textContent = content[0];
  message.textContent = content[1];
  if (typeof dialog.showModal === 'function') dialog.showModal();
  else window.alert(`${content[0]}\n\n${content[1]}`);
}
document.querySelectorAll('[data-feature]').forEach(el => el.addEventListener('click', e => {
  e.preventDefault();
  if (el.dataset.feature === 'phone') { window.location.href = './phone.html'; return; }
  if (el.dataset.feature === 'passkey') { window.location.href = './passkey.html'; return; }
  showNotice(el.dataset.feature);
}));
document.getElementById('notice-close').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', e => {if (e.target === dialog) dialog.close();});
goToSlide(0);
