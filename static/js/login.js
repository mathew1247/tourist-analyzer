/**
 * XploreElite - Database Authentication & Registration Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const tabSignIn = document.getElementById('tabSignIn');
  const tabSignUp = document.getElementById('tabSignUp');
  const signInContainer = document.getElementById('signInContainer');
  const registerContainer = document.getElementById('registerContainer');
  const linkToRegister = document.getElementById('linkToRegister');
  const linkToLogin = document.getElementById('linkToLogin');
  const alertBox = document.getElementById('loginAlert');

  // Sign In Form Elements
  const loginForm = document.getElementById('loginForm');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const rememberCheckbox = document.getElementById('rememberMe');

  // Register Form Elements
  const registerForm = document.getElementById('registerForm');
  const regFullName = document.getElementById('regFullName');
  const regEmail = document.getElementById('regEmail');
  const regPhone = document.getElementById('regPhone');
  const regPassword = document.getElementById('regPassword');

  // Check saved email
  const savedEmail = localStorage.getItem('saved_login_email');
  if (savedEmail && emailInput) {
    emailInput.value = savedEmail;
    if (rememberCheckbox) rememberCheckbox.checked = true;
  }

  function showAlert(message, type = 'danger') {
    if (!alertBox) return;
    alertBox.textContent = message;
    alertBox.className = `badge badge-${type}`;
    alertBox.style.display = 'block';
  }

  function hideAlert() {
    if (alertBox) alertBox.style.display = 'none';
  }

  // Tab Switchers
  function switchToSignIn() {
    hideAlert();
    tabSignIn.classList.add('active');
    tabSignUp.classList.remove('active');
    signInContainer.style.display = 'block';
    registerContainer.style.display = 'none';
    if (emailInput) emailInput.focus();
  }

  function switchToRegister() {
    hideAlert();
    tabSignUp.classList.add('active');
    tabSignIn.classList.remove('active');
    signInContainer.style.display = 'none';
    registerContainer.style.display = 'block';
    if (regFullName) regFullName.focus();
  }

  if (tabSignIn) tabSignIn.addEventListener('click', switchToSignIn);
  if (tabSignUp) tabSignUp.addEventListener('click', switchToRegister);
  if (linkToRegister) linkToRegister.addEventListener('click', switchToRegister);
  if (linkToLogin) linkToLogin.addEventListener('click', switchToSignIn);

  // ----------------------------------------------------
  // Sign In Submission (Real-Time Database Verification)
  // ----------------------------------------------------
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert();

      let isValid = true;
      const email = emailInput.value.trim();
      const password = passwordInput.value.trim();

      emailInput.classList.remove('is-invalid');
      passwordInput.classList.remove('is-invalid');

      if (!email) {
        emailInput.classList.add('is-invalid');
        isValid = false;
      }
      if (!password) {
        passwordInput.classList.add('is-invalid');
        isValid = false;
      }

      if (!isValid) return;

      const submitBtn = document.getElementById('loginBtn');
      const originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying credentials...';

      try {
        await TourismAPI.login(email, password);

        if (rememberCheckbox && rememberCheckbox.checked) {
          localStorage.setItem('saved_login_email', email);
        } else {
          localStorage.removeItem('saved_login_email');
        }

        showAlert('Credentials verified! Loading your dashboard...', 'success');
        showToast('Login successful!', 'success');

        setTimeout(() => {
          window.location.href = 'dashboard.html';
        }, 500);
      } catch (err) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        showAlert(err.message || 'Invalid email or password.');
      }
    });
  }

  // ----------------------------------------------------
  // Account Registration Submission (Saves into Database)
  // ----------------------------------------------------
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert();

      let isValid = true;
      const fullName = regFullName.value.trim();
      const email = regEmail.value.trim();
      const phone = regPhone.value.trim() || '+91 98765 43210';
      const password = regPassword.value.trim();

      [regFullName, regEmail, regPassword].forEach(el => el.classList.remove('is-invalid'));

      if (!fullName) {
        regFullName.classList.add('is-invalid');
        isValid = false;
      }
      if (!email || !email.includes('@')) {
        regEmail.classList.add('is-invalid');
        isValid = false;
      }
      if (!password || password.length < 6) {
        regPassword.classList.add('is-invalid');
        isValid = false;
      }

      if (!isValid) return;

      const registerBtn = document.getElementById('registerBtn');
      const originalText = registerBtn.innerHTML;
      registerBtn.disabled = true;
      registerBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating account in database...';

      try {
        await TourismAPI.register({
          fullName,
          username: fullName,
          email,
          phone,
          password
        });

        showAlert('Account registered successfully! Redirecting to dashboard...', 'success');
        showToast('Account created in database!', 'success');

        setTimeout(() => {
          window.location.href = 'dashboard.html';
        }, 600);
      } catch (err) {
        registerBtn.disabled = false;
        registerBtn.innerHTML = originalText;
        showAlert(err.message || 'Registration failed.');
      }
    });
  }
});
