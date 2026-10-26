/**
 * BBMKU University File Management System (UFMS)
 * Vanilla JavaScript UI Controller
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Sidebar Toggle for Mobile / Tablet
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
  const mobileMenuTrigger = document.getElementById('mobileMenuTrigger');
  const sidebarOverlay = document.getElementById('sidebarOverlay');

  function openSidebar() {
    if (sidebar) sidebar.classList.add('open');
    if (sidebarOverlay) sidebarOverlay.style.display = 'block';
    document.body.style.overflow = window.innerWidth <= 992 ? 'hidden' : '';
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('open');
    if (sidebarOverlay) sidebarOverlay.style.display = 'none';
    document.body.style.overflow = '';
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      if (sidebar && sidebar.classList.contains('open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (mobileMenuTrigger) {
    mobileMenuTrigger.addEventListener('click', function (e) {
      e.stopPropagation();
      openSidebar();
    });
  }

  if (sidebarCloseBtn) {
    sidebarCloseBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      closeSidebar();
    });
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', closeSidebar);
  }

  // Close sidebar on link click in mobile view
  document.querySelectorAll('.sidebar-nav .nav-item').forEach(link => {
    link.addEventListener('click', function () {
      if (window.innerWidth <= 992) {
        closeSidebar();
      }
    });
  });

  // 2. Modal Open/Close System
  document.querySelectorAll('[data-modal-target]').forEach(button => {
    button.addEventListener('click', function () {
      const targetId = this.getAttribute('data-modal-target');
      const modal = document.getElementById(targetId);
      if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
      }
    });
  });

  document.querySelectorAll('[data-modal-close]').forEach(button => {
    button.addEventListener('click', function () {
      const modal = this.closest('.modal-overlay');
      if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
      }
    });
  });

  // Close modal when clicking outside card
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function (e) {
      if (e.target === this) {
        this.classList.remove('show');
        document.body.style.overflow = '';
      }
    });
  });

  // 3. Confirmation Dialogs for critical actions
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', function (e) {
      const message = this.getAttribute('data-confirm') || 'Are you sure you want to proceed with this action?';
      if (!confirm(message)) {
        e.preventDefault();
        return false;
      }
    });
  });

  // 4. Alert Auto-Dismiss or Close Click
  document.querySelectorAll('.alert-close').forEach(closeBtn => {
    closeBtn.addEventListener('click', function () {
      const alert = this.closest('.alert');
      if (alert) {
        alert.style.transition = 'opacity 0.3s ease';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
      }
    });
  });

  // 5. Reset Filter Button Helper
  const resetFilterBtn = document.getElementById('resetFiltersBtn');
  if (resetFilterBtn) {
    resetFilterBtn.addEventListener('click', function (e) {
      e.preventDefault();
      const form = this.closest('form');
      if (form) {
        window.location.href = form.getAttribute('action') || window.location.pathname;
      }
    });
  }
});
