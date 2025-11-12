const accordion = document.getElementById('settings-accordion');

if (accordion) {
  const items = Array.from(accordion.querySelectorAll('.accordion-item'));

  const setExpandedState = (entry, expanded) => {
    const trigger = entry.querySelector('.accordion-trigger');
    const panel = entry.querySelector('.accordion-panel');

    trigger.setAttribute('aria-expanded', expanded ? 'true' : 'false');

    if (expanded) {
      panel.removeAttribute('hidden');
      entry.classList.add('active');
    } else {
      panel.setAttribute('hidden', '');
      entry.classList.remove('active');
    }
  };

  items.forEach((item) => {
    setExpandedState(item, item.classList.contains('active'));

    const trigger = item.querySelector('.accordion-trigger');
    trigger.addEventListener('click', () => {
      if (item.classList.contains('active')) {
        return;
      }

      items.forEach((entry) => {
        if (entry !== item) {
          setExpandedState(entry, false);
        }
      });

      setExpandedState(item, true);
    });
  });
}

document.querySelectorAll('.chip-group').forEach((group) => {
  group.querySelectorAll('.chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      group.querySelectorAll('.chip').forEach((c) => c.classList.remove('selected'));
      chip.classList.add('selected');
    });
  });
});

// Provide subtle pressed feedback for ghost buttons
const buttons = document.querySelectorAll('.btn');
buttons.forEach((button) => {
  button.addEventListener('mousedown', () => button.classList.add('pressed'));
  button.addEventListener('mouseup', () => button.classList.remove('pressed'));
  button.addEventListener('mouseleave', () => button.classList.remove('pressed'));
});
