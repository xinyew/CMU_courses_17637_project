'use strict';

function generate() {
  $.post(
    "/console/generate/",
    {
    },
    function (data) {
    }
  );
}


// AJAX calls
function getDiscussion(imageID) {
  let xhr = new XMLHttpRequest()
  xhr.onreadystatechange = function () {
    if (this.readyState != 4) {
      return
    }
    updateDiscussionBoard(xhr)
  }
  xhr.open("GET", "/get_discussion/" + imageID, true)
  xhr.send()
}


function updateDiscussionBoard(xhr) {
  if (xhr.status == 200) {
    let response = JSON.parse(xhr.responseText)
    updateDiscussions(response)
    return
  }

  if (xhr.status == 0) {
    displayError("Cannot connect to server")
    return
  }

  if (!xhr.getResponseHeader('content-type') == 'application/json') {
    displayError("Received status:" + xhr.status)
    return
  }

  let response = JSON.parse(xhr.responseText)
  if (response.hasOwnProperty('error')) {
    displayError(response.error)
    return
  }
}

function displayError(message) {
  $('#id_discussion_post_error').html(message)
}

function updateDiscussions(response) {
  $(response.comments).each(function () {
    let is_new_comment = true
    let comment_id = this.id
    let new_item_id = "id_discussion_wrap_" + comment_id
    $(".discussion_wrap").each(function () {
      if (new_item_id == this.id) {
        is_new_comment = false
      }
    })
    if (is_new_comment) {
      $("#id_discussions").prepend(
        '<div id="id_discussion_wrap_' + comment_id + '" class="discussion_wrap">' +
        '<div class="discussion_comment">' +
        '<div class="discussion_portrait">' +
        '<img src="/get_photo/' + this.user_id + ' class="rounded" width="40">' +
        '</div>' +
        '<div class="discussion_comment_conetent">' +
        '<div class="discussion_post_information">' +
        '<a href="/others_profile/' + this.user_id + '" class="discussion_commenter">' +
        this.first_name + ' ' + this.last_name +
        '</a>' +
        '<span class="discussion_date_time">' +
        this.date_created +
        '</span>' +
        '</div>' +
        '<div class="discussion_comment_text">' +
        this.text +
        '</div>' +
        '</div>' +
        '</div>' +
        '<div id="discussion_replies_' + comment_id + '" class="discussion_replies">' +
        '<div id="id_discussion_reply_input_group_' + comment_id + ' class="discussion_reply_input_group">' +
        '<div class="input-group">' +
        '<input type="text" class="form-control" placeholder="Type your comment here">' +
        '<button class="btn btn-outline-secondary" type="button" id="id_discussion_' + comment_id + '_reply_button_' + reply_id + '">' +
        'Comment' + '</button>' +
        '</div>' +
        '</div>' +
        '</div>' +
        '</div>'
      )
    }
  })
  $(response.replies).each(function () {
    let is_new_reply = true
    let reply_id = this.id
    let new_reply_id = "id_discussion_reply_" + reply_id
    $(".discussion_reply").each(function () {
      if (new_reply_id == this.id) {
        is_new_reply = false
      }
    })
    if (is_new_reply) {
      $("#id_discussion_replies_" + comment_id).prepend(
        '<div id="id_discussion_reply_' + reply_id + '" class="discussion_reply">' +
        '<div class="discussion_portrait">' +
        '<img src="/get_photo/' + this.user_id + ' class="rounded" width="40">' +
        '</div>' +
        '<div class="discussion_reply_conetent">' +
        '<div class="discussion_post_information">' +
        '<a href="/others_profile/' + this.user_id + '" class="discussion_commenter">' +
        this.first_name + ' ' + this.last_name +
        '</a>' +
        '<span class="discussion_date_time">' +
        this.date_created +
        '</span>' +
        '</div>' +
        '<div class="discussion_reply_text">' +
        this.text +
        '</div>' +
        '</div>' +
        '</div>'
      )
    }
  })
}