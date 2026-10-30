// The entry screen remains usable when autoplay is blocked or the video is unavailable.
document.addEventListener('DOMContentLoaded', () => {
  const video = document.querySelector('.welcome-video');
  if (!video) return;
  const play = video.play();
  if (play && typeof play.catch === 'function') play.catch(() => {});
});
