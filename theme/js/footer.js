document.addEventListener('DOMContentLoaded', function() {
  const content = document.querySelector('.content');
  if (!content) return;

  const footer = document.createElement('footer');
  footer.className = 'mdbook-footer';
  footer.innerHTML = `
      <div class="mdbook-footer__container">
          <div class="mdbook-footer__links">
              <a href="https://optimism.io/community-agreement">Community Agreement</a>
              <a href="https://optimism.io/terms">Terms of Service</a>
              <a href="https://optimism.io/data-privacy-policy">Privacy Policy</a>
          </div>
          <div class="mdbook-footer__copyright">
              © 2025 Optimism Foundation. All rights reserved.
          </div>
      </div>
  `;

  // Insert after the main content container
  document.body.appendChild(footer);
});