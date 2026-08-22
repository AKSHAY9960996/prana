document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('overlay');
  const hamburger = document.getElementById('hamburgerBtn');
  const main = document.querySelector('.main');

  // Restore saved desktop sidebar preference
  if (window.innerWidth > 760) {
    const isCollapsed = localStorage.getItem('sidebar_collapsed') === 'true';
    if (isCollapsed && sidebar && main) {
      sidebar.classList.add('collapsed');
      main.classList.add('expanded');
    }
  }

  function toggleSidebar() {
    if (window.innerWidth > 760) {
      // Desktop toggle
      const isCollapsed = sidebar.classList.toggle('collapsed');
      main.classList.toggle('expanded', isCollapsed);
      localStorage.setItem('sidebar_collapsed', isCollapsed ? 'true' : 'false');
    } else {
      // Mobile drawer toggle
      sidebar.classList.toggle('open');
      overlay.classList.toggle('open');
    }
  }

  function closeMobileSidebar() {
    if (sidebar) sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('open');
  }

  if (hamburger) hamburger.addEventListener('click', toggleSidebar);
  if (overlay) overlay.addEventListener('click', closeMobileSidebar);
});
