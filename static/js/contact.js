document.addEventListener("DOMContentLoaded", () => {
  buttonTimer();
  formSubmitLoad();
});

// Sets form submission button to active only after 3 seconds
function buttonTimer() {
  setTimeout(function () {
    const button = document.getElementById('contact-submit');
    if (button) {
      button.disabled = false;
      button.className = 'active-button';
    }
  }, 3000);
};

function formSubmitLoad() {
  const contactForm = document.getElementById('contact-form').addEventListener('submit', () => {
    console.log('Form submitted')
    const button = document.getElementById('contact-submit');
    button.className='inactive-button';
    button.disabled='true';
    const loadingDiv = document.createElement('div');
    const loadingText = document.createElement('span');
    const loadingSpinner = document.createElement('span');
    loadingText.textContent = 'Validating form...';
    loadingText.className='validation';
    loadingSpinner.textContent = '⧗';
    loadingSpinner.className='loading-spinner';
    button.after(loadingDiv);
    loadingDiv.appendChild(loadingText);
    loadingDiv.appendChild(loadingSpinner);
  });
};