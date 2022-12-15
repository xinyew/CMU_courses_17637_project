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
    success: function (response_data) {
      let template = document.createElement('template');
      template.innerHTML = response_data;
      let response_document = template.content;
      // Honestly this looping idea should have been used for all our functions...
      for (let response_elem of response_document.children) {
        let orig_elem = document.getElementById(response_elem.id);
        if (orig_elem !== null) {
          orig_elem.replaceWith(response_elem);
        } else {
          let label_buttons = document.getElementById('id_label_buttons');
          if (label_buttons !== null) {
            label_buttons.prepend(response_elem);
          }
        }
      }
    },
  });
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
      console.log(this.user_id)
      $("#id_discussions").prepend(
        `
        <div id="id_discussion_wrap_${comment_id}" class="discussion_wrap">
          <div class="discussion_comment">
            <div class="discussion_portrait">
              <img src="/get_portrait/${this.user_id}" class="rounded" width="40">
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
          <div id="id_discussion_replies_${comment_id}" class="discussion_replies">
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
                onclick="replyNew(${comment_id})">
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
    let comment_id = this.comment_id
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
            <img src="/get_portrait/${this.user_id}" class="rounded" width="40">
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

function updateRecentActivities(xhr) {
  if (xhr.status == 200) {
    let response = JSON.parse(xhr.responseText);
    updateActivities(response);
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

function updateActivities(response) {
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
      console.log(this.user_id)
      $("#id_discussions").prepend(
        `
        <div id="id_discussion_wrap_${comment_id}" class="discussion_wrap">
          <div class="discussion_comment">
            <div class="discussion_portrait">
              <img src="/get_portrait/${this.user_id}" class="rounded" width="40">
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
          <div id="id_discussion_replies_${comment_id}" class="discussion_replies">
          </div>
        </div>
        `
      );
    }
  });
  $(response.replies).each(function () {
    let comment_id = this.comment_id
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
            <img src="/get_portrait/${this.user_id}" class="rounded" width="40">
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

function replyNew(comment_id) {
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
  xhr.open("POST", "/reply_new/", true);
  xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhr.send("image_id=" + image_id + "&reply_text=" + replyText + "&comment_id=" + comment_id + "&csrfmiddlewaretoken=" + getCSRFToken());
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

function followUnfollow(user_id) {
  let xhr = new XMLHttpRequest()
  xhr.onreadystatechange = function () {
    if (this.readyState != 4) {
      return
    }
    updateFollowStatus(xhr)
  }

  xhr.open("POST", "/follow_unfollow/" + user_id, true)
  xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhr.send("user_id=" + user_id + "&csrfmiddlewaretoken=" + getCSRFToken());
}

function updateFollowStatus(xhr) {
  if (xhr.status == 200) {
    let response = JSON.parse(xhr.responseText);
    if (response.following) {
      $('#id_profile_card_button').html('Unfollow')
    } else {
      $('#id_profile_card_button').html('Follow')
    }
    $('#id_follower_num').html(response.following_num)
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

function getLucky() {
  let random = Math.floor(Math.random() * lucky_prompts.length)
  $('#id_prompt_input_text').val(lucky_prompts[random])
}

const lucky_prompts = ["3D render of a cute tropical fish in an aquarium on a dark blue background, digital art",
  "An armchair in the shape of an avocado",
  "An oil painting by Matisse of a humanoid robot playing chess",
  "An expressive oil painting of a basketball player dunking, depicted as an explosion of a nebula",
  "A photo of a silhouette of a person in a color lit desert at night",
  "A photo of a white fur monster standing in a purple room",
  "A blue orange sliced in half laying on a blue floor in front of a blue wall",
  "A 3D render of an astronaut walking in a green desert",
  "A futuristic neon lit cyborg face",
  "A computer from the 90s in the style of vaporwave",
  "A cartoon of a monkey in space",
  "A plush toy robot sitting against a yellow wall",
  "A bowl of soup that is also a portal to another dimension, digital art",
  "A van Gogh style painting of an American football player",
  "A sea otter with a pearl earring by Johannes Vermeer",
  "A hand drawn sketch of a Porsche 911",
  "High quality photo of a monkey astronaut",
  "A cyberpunk monster in a control room",
  "A photo of Michelangelo's sculpture of David wearing headphones djing",
  "An abstract painting of artificial intelligence",
  "An Andy Warhol style painting of a french bulldog wearing sunglasses",
  "A photo of a Samoyed dog with its tongue out hugging a white Siamese cat",
  "A photo of a teddy bear on a skateboard in Times Square",
  "An abstract oil painting of a river",
  "A futuristic cyborg poster hanging in a neon lit subway station",
  "An oil pastel drawing of an annoyed cat in a spaceship",
  "A sunlit indoor lounge area with a pool with clear water and another pool with translucent pastel pink water, next to a big window, digital art"]