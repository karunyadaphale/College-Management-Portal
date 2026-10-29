/**
 * College Management Portal - Frontend Scripts
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Auto-dismiss flash alert messages after 6 seconds
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      try {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      } catch (e) {
        // Fallback
        alert.style.display = 'none';
      }
    }, 6000);
  });

  // 2. Attendance Quick Selectors: "Mark All Present" & "Mark All Absent"
  const markAllPresentBtn = document.getElementById('markAllPresent');
  if (markAllPresentBtn) {
    markAllPresentBtn.addEventListener('click', function () {
      const presentRadios = document.querySelectorAll("input[type='radio'][value='Present']");
      presentRadios.forEach(function (radio) {
        radio.checked = true;
      });
    });
  }

  const markAllAbsentBtn = document.getElementById('markAllAbsent');
  if (markAllAbsentBtn) {
    markAllAbsentBtn.addEventListener('click', function () {
      const absentRadios = document.querySelectorAll("input[type='radio'][value='Absent']");
      absentRadios.forEach(function (radio) {
        radio.checked = true;
      });
    });
  }

  // 3. Quick Login Fill for Viva/Demo purposes
  const demoRoleBtns = document.querySelectorAll('.btn-demo-fill');
  demoRoleBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const usernameInput = document.getElementById('username');
      const passwordInput = document.getElementById('password');
      if (usernameInput && passwordInput) {
        usernameInput.value = btn.dataset.username || '';
        passwordInput.value = btn.dataset.password || '';
      }
    });
  });
});
