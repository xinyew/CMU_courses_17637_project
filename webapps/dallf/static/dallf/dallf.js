'use strict';

function generate(form, event) {
  event.preventDefault();
  let data = new FormData(form);
  $.ajax("/console/", {
    processData: false,
    contentType: false,
    method: "POST",
    data: data,
    success: function (response_data) {
      console.log(response_data);
    },
    error: function (request, error) {
      console.log(request);
      console.log(error);
    }
  });
}

function click_dropdown(elem, event) {
  var target = event.target;
  if (target instanceof Element && target.classList.contains('dropdown_selection__item')) {
    let old_target = elem.querySelector('.dropdown_selection__item.active');
    if (old_target !== null) {
      old_target.classList.remove('active');
    }
    target.classList.add('active');
    elem.dataset.text = target.textContent;
  }
}

function make_generate_form(event) {
  let data = event.formData;
  let elems_to_add = document.querySelectorAll('.dropdown_selection');
  for (let elem of elems_to_add) {
    data.set(elem.dataset.name, elem.dataset.text);
  }
}
