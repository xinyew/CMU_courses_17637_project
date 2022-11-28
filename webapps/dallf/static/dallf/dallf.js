function clickLabelButton(imageID) {
    console.log('id:', imageID)
    id = 'id_image_' + imageID + '_label_button'
    modal = 'id_image_' + imageID + '_label_popup'
    console.log(id)
    document.getElementById(id).click()
    $(modal).modal('show')
}