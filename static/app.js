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

  field.on('input', function(evt) {
    search(evt.target.value);
  });
});

