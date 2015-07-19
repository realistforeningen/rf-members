// Add JavaScript here
var member_names;

$(function() {
    var t = null;
    $("#membershipName").keyup(function(){
        if (t) {
            clearTimeout(t);
        }
        t = setTimeout("member_filter()", 200);
    });
});

function member_filter() {
  var q = $("#membershipName").val().toLowerCase();

  matching_names = [];

  if (q.length == 0) {
    $("#existingMembers").hide();
  } else {
    $.each(member_names, function(i, full_name) {
      names = full_name.split(" ");

      $.each(names, function(j, name) {
        if (name.toLowerCase().indexOf(q) >= 0) {
          // q is substring of name, add it to result list

          if ($.inArray(full_name, matching_names) == -1) {
            // full_name is not already matched
            matching_names.push(full_name);
          }
        }
      });
    });
  }

  if (matching_names.length != 0) {
    // Matches were found
    $("#existingMembersList").empty();

    $.each(matching_names, function(i, full_name) {
      $("#existingMembersList").append("<li>" + full_name + "</li>");
    });

    $("#existingMembers").show();
  }
}

$(document).ready(function() {
  $("#existingMembers").hide();

  $.get("/api/names", function(data) {
    member_names = data.member_names;
  });
});
