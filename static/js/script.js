$(document).ready(function () {

  // ---------- Dark / Light mode ----------
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem('theme', theme);
    $('#themeToggle i').attr('class', theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars');
  }

  applyTheme(localStorage.getItem('theme') || 'light');

  $('#themeToggle').on('click', function () {
    var current = $('html').attr('data-bs-theme');
    applyTheme(current === 'dark' ? 'light' : 'dark');
  });

  // ---------- Alerts auto hide (jQuery animation) ----------
  setTimeout(function () {
    $('.auto-dismiss').fadeOut(500, function () { $(this).remove(); });
  }, 4000);

  // ---------- PIN input: sirf digits ----------
  $('.pin-input').on('input', function () {
    this.value = this.value.replace(/\D/g, '');
  });

  // ---------- Form validation (password / PIN match) ----------
  function showError(form, msg) {
    form.find('.js-error').remove();
    form.prepend('<div class="alert alert-danger js-error">' + msg + '</div>');
  }

  $('form.js-validate').on('submit', function (e) {
    var form = $(this);

    var pass = form.find('#id_password, #id_new_password').val();
    var confirmPass = form.find('#id_confirm_password').val();
    if (pass !== undefined && confirmPass !== undefined && pass !== confirmPass) {
      e.preventDefault();
      showError(form, 'Passwords do not match.');
      return;
    }

    var pin = form.find('#id_pin').val();
    var confirmPin = form.find('#id_confirm_pin').val();
    if (pin !== undefined && pin.length !== 6) {
      e.preventDefault();
      showError(form, 'PIN must be exactly 6 digits.');
      return;
    }
    if (pin !== undefined && confirmPin !== undefined && pin !== confirmPin) {
      e.preventDefault();
      showError(form, 'PINs do not match.');
    }
  });

    // ---------- Delete confirm ----------
  $(document).on('submit', '.js-delete-form', function (e) {
    if (!confirm('Are you sure you want to delete this record?')) {
      e.preventDefault();
    }
  });

});