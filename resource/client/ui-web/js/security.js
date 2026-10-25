// Security helpers for CSRF and AJAX
(function() {
  if (typeof window.gwdCsrfToken !== 'string') {
    console.error('gwdCsrfToken not initialized; include after auth.php');
    return;
  }

  // HTML escape helper for use in JavaScript
  window.gwdEscape = function(str) {
    if (typeof str !== 'string') str = String(str);
    return str.replace(/[&<>"']/g, function(char) {
      return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[char];
    });
  };

  // Download de_GWD system backup (only preserved backup kind)
  window.gwdDownload = function() {
    var form = document.createElement('form');
    form.method = 'POST';
    form.action = './act/download.php';

    var input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'kind';
    input.value = 'de_GWD';
    form.appendChild(input);

    var token = document.createElement('input');
    token.type = 'hidden';
    token.name = 'csrf_token';
    token.value = window.gwdCsrfToken;
    form.appendChild(token);

    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
  };

  // Setup jQuery AJAX defaults for same-origin POST requests
  if (typeof jQuery !== 'undefined') {
    jQuery.ajaxPrefilter(function(options, originalOptions, jqXHR) {
      // Only apply to same-origin requests
      if (options.crossDomain === true || options.url.indexOf('://') > -1) {
        return;
      }

      // Convert GET to POST for same-origin state-changing calls
      if (options.type === undefined || options.type === 'GET') {
        options.type = 'POST';
      }

      // Add CSRF token for POST requests
      if (options.type === 'POST') {
        var data = options.data;
        if (typeof data === 'string') {
          options.data = data + '&csrf_token=' + encodeURIComponent(window.gwdCsrfToken);
        } else if (typeof data === 'object' && data !== null) {
          if (data instanceof FormData) {
            data.append('csrf_token', window.gwdCsrfToken);
          } else {
            data.csrf_token = window.gwdCsrfToken;
          }
        } else {
          options.data = 'csrf_token=' + encodeURIComponent(window.gwdCsrfToken);
        }
      }

      // Add X-CSRF-Token header for JSON/AJAX
      jqXHR.setRequestHeader('X-CSRF-Token', window.gwdCsrfToken);
      jqXHR.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    });
  }
})();
