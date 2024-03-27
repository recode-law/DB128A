function update_choice_visibility() {
    let should_be_hidden = document.getElementById('id_online_service_possible').checked !== true;

    document.getElementById('id_camera_perspectives').parentElement.hidden = should_be_hidden;
    document.getElementById('id_conferencing_software').parentElement.hidden = should_be_hidden;
}