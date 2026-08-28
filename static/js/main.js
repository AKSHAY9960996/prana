document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('overlay');
  const hamburger = document.getElementById('hamburgerBtn');
  const main = document.querySelector('.main');

  // Restore saved desktop sidebar preference
  if (window.innerWidth > 760) {
    const isCollapsed = localStorage.getItem('sidebar_collapsed') === 'true';
    if (isCollapsed) {
      document.documentElement.classList.add('sidebar-is-collapsed');
      if (sidebar) sidebar.classList.add('collapsed');
      if (main) main.classList.add('expanded');
    }
  }

  function toggleSidebar() {
    if (window.innerWidth > 760) {
      // Desktop toggle
      const isCollapsed = document.documentElement.classList.toggle('sidebar-is-collapsed');
      if (sidebar) sidebar.classList.toggle('collapsed', isCollapsed);
      if (main) main.classList.toggle('expanded', isCollapsed);
      localStorage.setItem('sidebar_collapsed', isCollapsed ? 'true' : 'false');
    } else {
      // Mobile drawer toggle
      if (sidebar) sidebar.classList.toggle('open');
      if (overlay) overlay.classList.toggle('open');
    }
  }

  function closeMobileSidebar() {
    if (sidebar) sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('open');
  }

  if (hamburger) hamburger.addEventListener('click', toggleSidebar);
  if (overlay) overlay.addEventListener('click', closeMobileSidebar);
});
