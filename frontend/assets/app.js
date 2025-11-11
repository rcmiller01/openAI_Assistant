const accordion = document.getElementById('settings-accordion');
const items = Array.from(accordion.querySelectorAll('.accordion-item'));

items.forEach((item) => {
  const trigger = item.querySelector('.accordion-trigger');
  trigger.addEventListener('click', () => {
    if (item.classList.contains('active')) {
      return;
    }

    items.forEach((entry) => entry.classList.remove('active'));
    item.classList.add('active');
  });
});

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
