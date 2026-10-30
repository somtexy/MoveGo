/* MoveGo Option 4: replace existing back glyphs with an accessible SVG chevron.
   Existing href, onclick, and IDs are preserved. */
(() => {
  'use strict';
  const icon = '<svg class="movego-chevron-left" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="m15 18-6-6 6-6"/></svg>';
  function apply() {
    const candidates = document.querySelectorAll('a.back,button.back,#search-back,[data-movego-back]');
    candidates.forEach(control => {
      if (control.dataset.movegoBackReady === '1') return;
      // Don't wipe extra action labels or children on a control: opt-in only if dedicated back control.
      if (control.querySelector('input,select,textarea')) return;
      control.innerHTML = icon;
      control.dataset.movegoBackReady = '1';
      if (!control.getAttribute('aria-label')) control.setAttribute('aria-label', 'Go back');
      if (control.tagName === 'BUTTON' && !control.getAttribute('type')) control.setAttribute('type', 'button');
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply, {once:true});
  else apply();
})();
