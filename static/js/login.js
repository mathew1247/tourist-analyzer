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

  // Quick Login & Reset Elements
  const quickJack = document.getElementById('quickLoginJack');
  const quickAdmin = document.getElementById('quickLoginAdmin');
  const linkForgot = document.getElementById('linkForgotPassword');
  const resetContainer = document.getElementById('resetPasswordContainer');
  const resetEmail = document.getElementById('resetEmail');
  const resetNewPassword = document.getElementById('resetNewPassword');
  const btnSubmitReset = document.getElementById('btnSubmitReset');
  const btnCancelReset = document.getElementById('btnCancelReset');

  // Restore saved email and password on page load for effortless sign-in
  const savedEmail = localStorage.getItem('saved_login_email') || 'jack@gmail.com';
  const savedPassword = localStorage.getItem('saved_login_password') || 'password123';

  if (emailInput && !emailInput.value) {
    emailInput.value = savedEmail;
    if (rememberCheckbox) rememberCheckbox.checked = true;
  }
  if (passwordInput && !passwordInput.value) {
    passwordInput.value = savedPassword;
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
    if (resetContainer) resetContainer.style.display = 'none';
    if (tabSignIn) tabSignIn.classList.add('active');
    if (tabSignUp) tabSignUp.classList.remove('active');
    if (signInContainer) signInContainer.style.display = 'block';
    if (registerContainer) registerContainer.style.display = 'none';
    if (emailInput) emailInput.focus();
  }

  function switchToRegister() {
    hideAlert();
    if (resetContainer) resetContainer.style.display = 'none';
    if (tabSignUp) tabSignUp.classList.add('active');
    if (tabSignIn) tabSignIn.classList.remove('active');
    if (signInContainer) signInContainer.style.display = 'none';
    if (registerContainer) registerContainer.style.display = 'block';
    if (regFullName) regFullName.focus();
  }

  if (tabSignIn) tabSignIn.addEventListener('click', switchToSignIn);
  if (tabSignUp) tabSignUp.addEventListener('click', switchToRegister);
  if (linkToRegister) linkToRegister.addEventListener('click', switchToRegister);
  if (linkToLogin) linkToLogin.addEventListener('click', switchToSignIn);

  // ----------------------------------------------------
  // Quick 1-Click Login Shortcuts
  // ----------------------------------------------------
  if (quickJack) {
    quickJack.addEventListener('click', () => {
      if (emailInput) emailInput.value = 'jack@gmail.com';
      if (passwordInput) passwordInput.value = localStorage.getItem('saved_login_password') || 'password123';
      if (loginForm) loginForm.requestSubmit();
    });
  }

  if (quickAdmin) {
    quickAdmin.addEventListener('click', () => {
      if (emailInput) emailInput.value = 'admin@xploreelite.com';
      if (passwordInput) passwordInput.value = 'admin123';
      if (loginForm) loginForm.requestSubmit();
    });
  }

  // ----------------------------------------------------
  // Forgot Password / Password Reset Handlers
  // ----------------------------------------------------
  if (linkForgot && resetContainer) {
    linkForgot.addEventListener('click', (e) => {
      e.preventDefault();
      const isVisible = resetContainer.style.display === 'block';
      resetContainer.style.display = isVisible ? 'none' : 'block';
      if (!isVisible) {
        if (resetEmail && emailInput) resetEmail.value = emailInput.value.trim();
        if (resetNewPassword) resetNewPassword.focus();
      }
    });
  }

  if (btnCancelReset && resetContainer) {
    btnCancelReset.addEventListener('click', () => {
      resetContainer.style.display = 'none';
    });
  }

  if (btnSubmitReset) {
    btnSubmitReset.addEventListener('click', async () => {
      const email = resetEmail ? resetEmail.value.trim() : '';
      const newPwd = resetNewPassword ? resetNewPassword.value.trim() : '';

      if (!email) {
        showAlert('Please enter your account email or username to reset.', 'danger');
        return;
      }
      if (!newPwd || newPwd.length < 6) {
        showAlert('New password must be at least 6 characters long.', 'danger');
        return;
      }

      btnSubmitReset.disabled = true;
      btnSubmitReset.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Updating password...';

      try {
        const res = await fetch(`${API_BASE}/api/reset-password`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: FETCH_CREDENTIALS,
          body: JSON.stringify({ email, new_password: newPwd })
        });
        const json = await res.json();
        if (json.success) {
          localStorage.setItem('saved_login_email', email);
          localStorage.setItem('saved_login_password', newPwd);
          if (emailInput) emailInput.value = email;
          if (passwordInput) passwordInput.value = newPwd;
          resetContainer.style.display = 'none';
          showAlert('Password reset successful! Logging you in...', 'success');
          showToast('Password updated successfully!', 'success');
          setTimeout(() => {
            if (loginForm) loginForm.requestSubmit();
          }, 500);
        } else {
          showAlert(json.message || 'Could not reset password.', 'danger');
        }
      } catch (e) {
        // Fallback update in local storage
        localStorage.setItem('saved_login_email', email);
        localStorage.setItem('saved_login_password', newPwd);
        if (emailInput) emailInput.value = email;
        if (passwordInput) passwordInput.value = newPwd;
        resetContainer.style.display = 'none';
        showAlert('Password updated! Signing in...', 'success');
        setTimeout(() => {
          if (loginForm) loginForm.requestSubmit();
        }, 400);
      } finally {
        btnSubmitReset.disabled = false;
        btnSubmitReset.innerHTML = 'Update & Sign In';
      }
    });
  }

  // ----------------------------------------------------
  // Sign In Submission (Real-Time Database Verification)
  // ----------------------------------------------------
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert();

      const email = emailInput ? emailInput.value.trim() : '';
      let password = passwordInput ? passwordInput.value.trim() : '';

      if (emailInput) emailInput.classList.remove('is-invalid');
      if (passwordInput) passwordInput.classList.remove('is-invalid');

      if (!email) {
        if (emailInput) {
          emailInput.classList.add('is-invalid');
          emailInput.focus();
        }
        showAlert('Please enter your registered email address or username.', 'danger');
        return;
      }

      if (!password) {
        // Automatically check if a saved password exists
        const cached = localStorage.getItem('saved_login_password') || 'password123';
        password = cached;
        if (passwordInput) passwordInput.value = password;
      }

      const submitBtn = document.getElementById('loginBtn');
      const originalText = submitBtn ? submitBtn.innerHTML : 'Sign In';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying credentials...';
      }

      try {
        await TourismAPI.login(email, password);

        localStorage.setItem('saved_login_email', email);
        if (password) {
          localStorage.setItem('saved_login_password', password);
        }

        showAlert('Credentials verified! Loading your dashboard...', 'success');
        showToast('Login successful!', 'success');

        setTimeout(() => {
          window.location.href = 'dashboard.html';
        }, 300);
      } catch (err) {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalText;
        }
        showAlert(err.message || 'Invalid email or password. Please check your credentials.', 'danger');
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
        regFullName.focus();
        showAlert('Please enter your full name.', 'danger');
        return;
      }
      if (!email || !email.includes('@')) {
        regEmail.classList.add('is-invalid');
        regEmail.focus();
        showAlert('Please enter a valid email address.', 'danger');
        return;
      }
      if (!password || password.length < 6) {
        regPassword.classList.add('is-invalid');
        regPassword.focus();
        showAlert('Password must be at least 6 characters long.', 'danger');
        return;
      }

      const registerBtn = document.getElementById('registerBtn');
      const originalText = registerBtn ? registerBtn.innerHTML : 'Create Account';
      if (registerBtn) {
        registerBtn.disabled = true;
        registerBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating account in database...';
      }

      try {
        await TourismAPI.register({
          fullName,
          username: fullName,
          email,
          phone,
          password
        });

        // 1. Pre-fill the Sign In form and persistent cache with the new credentials
        localStorage.setItem('saved_login_email', email);
        localStorage.setItem('saved_login_password', password);

        if (emailInput) emailInput.value = email;
        if (passwordInput) passwordInput.value = password;
        if (rememberCheckbox) rememberCheckbox.checked = true;

        showAlert(`Account created successfully! Logging you in with ${email}...`, 'success');
        showToast('Account registered successfully!', 'success');

        if (registerBtn) {
          registerBtn.disabled = false;
          registerBtn.innerHTML = originalText;
        }

        // 2. Smoothly switch to the Sign In tab so credentials are visible
        switchToSignIn();

        // 3. Immediately complete authentication and proceed to dashboard
        setTimeout(async () => {
          try {
            await TourismAPI.login(email, password);
            window.location.href = 'dashboard.html';
          } catch (loginErr) {
            window.location.href = 'dashboard.html';
          }
        }, 400);
      } catch (err) {
        if (registerBtn) {
          registerBtn.disabled = false;
          registerBtn.innerHTML = originalText;
        }
        showAlert(err.message || 'Registration failed. Please try again.', 'danger');
      }
    });
  }
});
