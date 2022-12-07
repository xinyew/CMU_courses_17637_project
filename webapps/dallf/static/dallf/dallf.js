'use strict';

function click_dropdown(elem, event) {
  var target = event.target;
  if (target instanceof Element && target.classList.contains('dropdown_selection__item')) {
    let old_target = elem.querySelector('.dropdown_selection__item.active');
    if (old_target !== null) {
      old_target.classList.remove('active');
    }
    target.classList.add('active');
  }
}


// AJAX calls
function getDiscussion() {
  // get the id of the only one element of discussions class from
  // <div id="id_discussions_{{recent_images.0.id}}" class="discussions">
  let imageID = ($('.discussions')[0].id).split('_')[2];

  let xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function () {
    if (this.readyState != 4) {
      return;
    }
    updateDiscussionBoard(xhr);
  };
  xhr.open("GET", "/get_discussion/" + imageID, true);
  xhr.send();
}


function updateDiscussionBoard(xhr) {
  if (xhr.status == 200) {
    let response = JSON.parse(xhr.responseText);
    updateDiscussions(response);
    return;
  }

  if (xhr.status == 0) {
    displayError("Cannot connect to server");
    return;
  }

  if (!xhr.getResponseHeader('content-type') == 'application/json') {
    displayError("Received status:" + xhr.status);
    return;
  }

  let response = JSON.parse(xhr.responseText);
  if (response.hasOwnProperty('error')) {
    displayError(response.error);
    return;
  }
}

function displayError(message) {
  $('#id_discussion_post_error').html(message);
}

function updateDiscussions(response) {
  // get the id of the only one element of discussions class from
  // <div id="id_discussions_{{recent_images.0.id}}" class="discussions">
  let image_id = ($('.discussions')[0].id).split('_')[2];
  $(response.comments).each(function () {
    let is_new_comment = true;
    let comment_id = this.id;
    let new_item_id = "id_discussion_wrap_" + comment_id;
    $(".discussion_wrap").each(function () {
      if (new_item_id == this.id) {
        is_new_comment = false;
      }
    });
    if (is_new_comment) {
      $("#id_discussions").prepend(
        `
        <div id="id_discussion_wrap_${comment_id}" class="discussion_wrap">
          <div class="discussion_comment">
            <div class="discussion_portrait">
              <img src="/get_photo/${this.user_id} class="rounded" width="40">
            </div>
            <div class="discussion_comment_conetent">
              <div class="discussion_post_information">
                <a href="/others_profile/${this.user_id}" class="discussion_commenter">
                  ${this.first_name} ${this.last_name}
                </a>
                <span class="discussion_date_time">
                  ${this.date_created}
                </span>
              </div>
              <div class="discussion_comment_text">
                ${this.text}
              </div>
            </div>
          </div>
          <div id="discussion_replies_${comment_id}" class="discussion_replies">
          </div>
          <div class="discussion_reply_input_group discussion_replies">
            <div class="input-group">
              <input
                type="text"
                class="form-control"
                id="id_discussion_${comment_id}_reply_text"
                placeholder="Type your comment here">
              <button
                class="btn btn-outline-secondary"
                type="button"
                id="id_discussion_${comment_id}_reply_button"
                onclick="replyNew(${image_id}, ${comment_id})">
                Comment
              </button>
            </div>
          </div>
        </div>

        <div class="discussion_wrap container">
          <div class="input-group">
            <input
              type="text"
              class="form-control"
              id="id_discussion_comment_text"
              placeholder="Type your comment here">
            <button
              class="btn btn-outline-secondary"
              type="button"
              id="id_discussion_comment_button"
              onclick="commentNew(${image_id})">
              Comment
            </button>
          </div>
        </div>
        `
      );
    }
  });
  $(response.replies).each(function () {
    let is_new_reply = true;
    let reply_id = this.id;
    let new_reply_id = `id_discussion_reply_${reply_id}`;
    $(".discussion_reply").each(function () {
      if (new_reply_id == this.id) {
        is_new_reply = false;
      }
    });
    if (is_new_reply) {
      $(`#id_discussion_replies_${comment_id}`).append(
        `
        <div id="id_discussion_reply_${reply_id}" class="discussion_reply">
          <div class="discussion_portrait">
            <img src="/get_photo/${this.user_id}" class="rounded" width="40">
          </div>
          <div class="discussion_reply_conetent">
            <div class="discussion_post_information">
              <a href="/others_profile/${this.user_id}" class="discussion_commenter">
                ${this.first_name} ${this.last_name}
              </a>
              <span class="discussion_date_time">
                ${this.date_created}
              </span>
            </div>
            <div class="discussion_reply_text">
              ${this.text}
            </div>
          </div>
        </div>
        `
      );
    }
  });
}

function commentNew(click_id) {
  let commentTextInputID = '#id_discussion_comment_text';
  let commentTextElement = $(commentTextInputID);
  let commentText = commentTextElement.val();
  commentTextElement.val('');
  displayError('');

  let xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function () {
    if (this.readyState != 4) {
      return;
    }
    updateDiscussionBoard(xhr);
    xhr.open("POST", "/new_comment", true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.send("comment_text=" + commentText + "&image_id=" + click_id + "&csrfmiddlewaretoken=" + getCSRFToken());
  };
}

function replyNew(image_id, comment_id) {
  let replyTextInputID = '#id_discussion_' + comment_id + '_reply_text';
  let replyTextElement = $(replyTextInputID);
  let replyText = replyTextElement.val();
  replyTextElement.val('');
  displayError('');

  let xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function () {
    if (this.readyState != 4) {
      return;
    }
    updateDiscussionBoard(xhr);
    xhr.open("POST", "/new_reply", true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.send("reply_text=" + replyText + "&image_id=" + image_id + "&comment_id=" + comment_id + "&csrfmiddlewaretoken=" + getCSRFToken());
  };
}

function getFollowers() {
  let xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function () {
    if (this.readyState != 4) {
      return;
    }
    updateProfilePage(xhr);
  };

  xhr.open("GET", "/get_follower", true);
  xhr.send();
}

function updateProfilePage() {

}

function getCSRFToken() {
  let cookies = document.cookie.split(";");
  for (let i = 0; i < cookies.length; i++) {
    let c = cookies[i].trim();
    if (c.startsWith("csrftoken=")) {
      return c.substring("csrftoken=".length, c.length);
    }
  }
  return "unknown";
}
