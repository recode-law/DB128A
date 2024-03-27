function changeVisibility(passwordId) {
    let passwordElement = document.getElementById(passwordId);
    if (passwordElement.getAttribute('type') === 'text') {
        passwordElement.setAttribute('type', 'password');
    } else {
        passwordElement.setAttribute('type', 'text');
    }

    let eyeElement = document.getElementById(`${passwordId}Eye`);
    if (eyeElement.className === 'bi bi-eye-slash-fill') {
        eyeElement.className = 'bi bi-eye-fill';
    } else {
        eyeElement.className = 'bi bi-eye-slash-fill';
    }
}