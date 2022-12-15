'use strict';

function click_dropdown(event) {
  var elem = event.currentTarget;
  var target = event.target;
  if (target instanceof Element && target.classList.contains('dropdown_selection__item')) {
    let old_target = elem.querySelector('.dropdown_selection__item.active');
    if (old_target !== null) {
      old_target.classList.remove('active');
    }
    target.classList.add('active');
  }
}


function process_dropdowns(event) {
  var form = event.currentTarget;
  let data = event.formData;
  let elems_to_add = form.querySelectorAll('.dropdown_selection');
  for (let elem of elems_to_add) {
    let text = elem.querySelector('.dropdown_selection__item.active').textContent;
    data.set(elem.dataset.name, text);
  }
}


// AJAX calls


function publish(elem, id) {
  let state = elem.hasAttribute('data-image_button_bundle--show_active');
  $.ajax(`/images/${id}/publish/`, {
    type: "POST",
    data: {
      publish: !state,
      csrfmiddlewaretoken: CSRF_TOKEN,
    },
    success: function () {
      elem.toggleAttribute('data-image_button_bundle--show_active', !state);
    }
  });
}


function favorite(elem, id) {
  let state = elem.hasAttribute('data-image_button_bundle--show_active');
  $.ajax(`/images/${id}/favorite/`, {
    type: "POST",
    data: {
      favorite: !state,
      csrfmiddlewaretoken: CSRF_TOKEN,
    },
    success: function () {
      elem.toggleAttribute('data-image_button_bundle--show_active', !state);
    }
  });
}


function label(form, event, id) {
  let data = new FormData(form);
  data.set(event.submitter.name, event.submitter.value);
  data.set("csrfmiddlewaretoken", CSRF_TOKEN);
  $.ajax(`/images/${id}/label/`, {
    processData: false,
    contentType: false,
    method: "POST",
    data: data,
    success: function () {
    },
  });
}

function updateDiscussionBoard(xhr) {
  console.log(xhr.status)
  if (xhr.status == 200) {
    let response = JSON.parse(xhr.responseText);
    console.log(response)
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
    console.log(is_new_comment)
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
                placeholder="Type your reply here">
              <button
                class="btn btn-outline-secondary"
                type="button"
                id="id_discussion_${comment_id}_reply_button"
                onclick="replyNew(${image_id}, ${comment_id})">
                Reply
              </button>
            </div>
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

function commentNew() {
  let click_id = ($('.image_button_active')[0].id).split('_')[2];
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
  };
  xhr.open("POST", "/comment_new/", true);
  xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhr.send("comment_text=" + commentText + "&image_id=" + click_id + "&csrfmiddlewaretoken=" + getCSRFToken());
}

function replyNew() {
  let image_id = ($('.image_button_active')[0].id).split('_')[2];
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
  };
  xhr.open("POST", "/new_reply", true);
  xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhr.send("reply_text=" + replyText + "&image_id=" + image_id + "&comment_id=" + comment_id + "&csrfmiddlewaretoken=" + getCSRFToken());
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
