$(function() {
  var field = $('#membershipName');
  var header = $('#memberships-search-header');
  var defaultHeader = header.text();
  var container = $('#memberships-search-container');

  // Since we send search requests async this is a possible set of events:
  //   - User types "m"
  //   - (1) We request search?q=m
  //   - User types "a"
  //   - (2) We request search?q=ma
  //   - We get the response from (2)
  //   - We get the response from (1)
  //
  // In this case we want to make sure the last response
  // does not overwrite the reponse from (2).
  var currRequest = 0;
  var currResponse = 0;

  function search(query) {
    var id = ++currRequest;

    var xhr = $.ajax('/memberships/search', {
      data: { q: query }
    });

    xhr.done(function() {
      if (id <= currResponse) {
        // A newer response was already rendered.
        return;
      }

      currResponse = id;
      container.html(xhr.responseText);
      if (query) {
        header.text("Search results for " + query);
      } else {
        header.text(defaultHeader);
      }
    });
  }
  
  var delay = 200;
  var delayTimeout;

  field.on('input', function(evt) {
    if (delayTimeout) {
      clearTimeout(delayTimeout);
    }

    delayTimeout = setTimeout(function() {
      search(evt.target.value);
      delayTimeout = null;
    }, delay);
  });

  field.on('keydown', function(evt) {
    if (evt.which == 13) {
      // Prevent enter
      evt.preventDefault();
    }
  });

  function updateStartedAt(dom) {
    var seconds = (new Date).valueOf()/1000 - dom.data('started-at');
    var total_minutes = (seconds/60)|0;
    var minutes = total_minutes%60;
    var hours = (total_minutes/60)|0;
    var text;
    if (hours) {
      text = hours + "h " + minutes + "m";
    } else {
      text = minutes + "m";
    }

    dom.text(text);
  }

  $('[data-started-at]').each(function() {
    var dom = $(this);
    updateStartedAt(dom);
    setInterval(function() {
      updateStartedAt(dom);
    }, 5000);
  });
});

